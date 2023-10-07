"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and creates the necessary
Blueprint, and all the associated files.
"""

from datetime import datetime
from json import dump as json_dump, loads, JSONDecodeError
from os import environ
from pathlib import Path
from re import compile as re_compile, sub as re_sub, IGNORECASE
from shutil import copy as copy_file, unpack_archive, ReadError
from sys import exit as sys_exit
from typing import Optional

from requests import get

from src.database.db import create_new_blueprint


ROOT = Path(__file__).parent.parent
BLUEPRINT_FOLDER = ROOT / 'blueprints'
TEMP_PREVIEW_FILE = ROOT / 'preview.jpg'
TEMP_FILE = ROOT / 'tmp'
TEMP_DIRECTORY = ROOT / 'unzipped'
PATH_SAFE_TRANSLATION = str.maketrans({
    '?': '!',
    '<': '',
    '>': '',
    ':':' -',
    '"': '',
    '|': '',
    '*': '-',
    '/': '+',
    '\\': '+',
})


def get_blueprint_folders(series_name: str) -> tuple[str, str]:
    """
    Get the path-safe name for the given Series name.

    >>> get_blueprint_folders('The Expanse (2015)')
    ('E', 'The Expanse (2015)')
    >>> get_blueprint_folders('Demon Slayer: Kimetsu no Yaiba (2018)')
    ('D', 'Demon Slayer - Kimetsu no Yaiba (2018)')

    Args:
        series_name: Name of the Series.

    Returns:
        Tuple of the parent letter subfolder and the Path-safe name with
        prefix a/an/the and any illegal characters removed.
    """

    clean_name = str(series_name).translate(PATH_SAFE_TRANSLATION)
    sort_name = re_sub(r'^(a|an|the)(\s)', '', clean_name, flags=IGNORECASE)

    return sort_name[0].upper(), clean_name


def parse_database_ids(ids: str) -> dict:
    """
    Parse the given database ID strings into a dictionary of database
    IDs.

    >>> parse_database_ids('imdb:tt1234')
    {'imdb': 'tt1234'}
    >>> parse_database_ids('imdb:tt9876,tmdb:1234')
    {'imdb': 'tt9876', 'tmdb': 1234}
    """

    # No IDs specified, return empty dictionary
    if '_No response_' in ids or not ids:
        return {}

    # Parse each comma-separated ID
    database_ids = {}
    for id_substr in ids.split(','):
        try:
            id_type, id_ = id_substr.split(':')
        except ValueError as exc:
            print(f'Invalid database IDs {exc}')
            continue

        # Store as int if all digits, otherwise str
        database_ids[id_type] = int(id_) if id_.isdigit() else id_

    return database_ids


def parse_submission(data: Optional[dict] = None) -> dict:
    """
    Parse the submission from the `ISSUE_BODY` and `ISSUE_CREATOR`
    environment variables into a dictionary of submission data.

    Args:
        data: Data set to use instead of the environment variable. For
            manual importing.

    Returns:
        Data (as a dictionary) of the given submission.
    """

    # Parse issue from environment variable
    if data is None:
        try:
            content = loads(environ.get('ISSUE_BODY'))
            print(f'Parsed issue JSON as:\n{content}')
        except JSONDecodeError as exc:
            print(f'Unable to parse Context as JSON')
            print(exc)
            sys_exit(1)

        # Get the issue's author and the body (the issue text itself)
        creator = environ.get('ISSUE_CREATOR', 'CollinHeist')

        # Extract the data from the issue text
        issue_regex = re_compile(
            r'^### Series Name\s+(?P<series_name>.+)\s+'
            r'### Series Year\s+(?P<series_year>\d+)\s+'
            r'### Series Database IDs\s+(?P<database_ids>\d+)\s+'
            r'### Creator Username\s+(?P<creator>.+)\s+'
            r'### Blueprint Description\s+(?P<description>[\s\S]*)\s+'
            r'### Blueprint\s+```json\s+(?P<blueprint>[\s\S]*?)```\s+'
            r'### Preview Title Card\s+.*?\[.*\]\((?P<preview_url>.+)\)\s+'
            r'### Zip of Font Files\s+(_No response_|\[.+?\]\((?P<font_zip>http[^\s\)]+)\))\s*$'
        )

        # If data cannot be extracted, exit
        if not (data := issue_regex.match(content)):
            print(f'Unable to parse Blueprint from Issue')
            print(f'{content=!r}')
            sys_exit(1)

    # Get each variable from the issue
    data = {'font_zip': '_No response_'} | data
    # print(f'{data=}')
    series_name = data['series_name'].strip()
    series_year = data['series_year']
    database_ids = data['database_ids']
    creator = (creator if '_No response_' in data['creator'] else data['creator']).strip()
    description = data['description']
    blueprint = data['blueprint']
    preview_url = data['preview_url']
    if data.get('font_zip') is None or '_No response_' in data['font_zip']:
        font_zip_url = None
    else:
        font_zip_url = data['font_zip']
    # print(f'Raw parsed data: {series_name=}\n[{series_year=}\n{creator=}\n{description=}\n{preview_url=}\n{font_zip_url=}')

    # Parse blueprint as JSON
    try:
        blueprint = loads(blueprint)
    except JSONDecodeError:
        print(f'Unable to parse blueprint as JSON')
        print(f'{blueprint=!r}')
        sys_exit(1)

    # Clean up description
    description = [line.strip() for line in description.splitlines() if line.strip()]

    return {
        'series_name': series_name,
        'series_year': series_year,
        'database_ids': parse_database_ids(database_ids),
        'creator': creator,
        'preview_url': preview_url,
        'font_zip_url': font_zip_url,
        'blueprint': blueprint | {
            'creator': creator,
            'description': description,
        }
    }


def download_preview(url: str, blueprint_subfolder: Path):
    """
    Download the preview image at the given URL and write it to the
    Blueprint folder. This writes the image as `preview.jpg`.

    Args:
        url: URL to the preview file to download.
        blueprint_subfolder: Subfolder of the Blueprint to download the
            preview file into.
    """

    # Download preview
    if not (response := get(url, timeout=30)).ok:
        print(f'Unable to download preview file from "{url}"')
        print(response.content)
        sys_exit(1)
    print(f'Downloaded preview "{url}"')

    # Copy preview into blueprint folder
    TEMP_PREVIEW_FILE.write_bytes(response.content)
    copy_file(TEMP_PREVIEW_FILE, blueprint_subfolder / 'preview.jpg')
    # print(f'Copied "{url}" into blueprints/{letter}/{folder_name}/{blueprint.id}/preview.jpg')


def download_font_files(zip_url: str, blueprint_subfolder: Path) -> None:
    """
    Download any font files in the ZIP located at the given URL and
    write them in the given Blueprint folder.

    Args:
        zip_url: URL to the Font zip file to download.
        blueprint_subfolder: Subfolder of the Blueprint to download
            these Font files into.
    """

    # Download any font zip files if provided
    if zip_url is not None:
        if not (response := get(zip_url, timeout=30)).ok:
            print(f'Unable to download zip from "{zip_url}"')
            print(response.content)
            sys_exit(1)
        print(f'Downloaded "{zip_url}"')
        zip_content = response.content
        
        # Write zip to file
        uploaded_filename = zip_url.rsplit('/', maxsplit=1)[-1]
        downloaded_file = ROOT / uploaded_filename
        downloaded_file.write_bytes(zip_content)

        try:
            unpack_archive(downloaded_file, TEMP_DIRECTORY)
        except (ValueError, ReadError):
            print(f'Unable to unzip provided files from "{zip_url}"')
            sys_exit(1)

        print(f'Unzipped {[file.name for file in TEMP_DIRECTORY.glob("*")]}')

        for file in TEMP_DIRECTORY.glob('*'):
            if file.is_dir():
                print(f'Skipping directory [zip]/{file.name}')
                continue

            copy_file(file, blueprint_subfolder / file.name)
            # print(f'Copied [zip]/{file.name} into blueprints/{letter}/{folder_name}/{id_}/{file.name}')


def parse_and_create_blueprint():
    """
    Parse the Blueprint submission from the environment variables, add
    the resulting Series and Blueprint to the Blueprints database, and
    write the Blueprint files to the appropriate Blueprint subfolder(s).
    """

    # Parse submission, get associated Series and Blueprint SQL objects
    submission = parse_submission()
    fallback_path_name = get_blueprint_folders(
        f'{submission["series_name"]} ({submission["series_year"]})'
    )[1]
    series, blueprint = create_new_blueprint(
        submission['series_name'], submission['series_year'],
        fallback_path_name, submission['database_ids'], submission['creator'],
        submission['blueprint'],
    )

    # Get the associated folder for this Series
    letter, folder_name = get_blueprint_folders(f'{series.name} ({series.year})')

    # Create Series folder
    series_subfolder = BLUEPRINT_FOLDER / letter / folder_name
    series_subfolder.mkdir(exist_ok=True, parents=True)

    # Create Blueprint ID folder
    blueprint_subfolder = series_subfolder / str(blueprint.blueprint_number)
    blueprint_subfolder.mkdir(exist_ok=True, parents=True)
    print(f'Created blueprints/{letter}/{folder_name}/{blueprint.blueprint_number}')

    # Download preview
    download_preview(submission['preview_url'], blueprint_subfolder)

    # Add preview image to blueprint
    submission['blueprint']['preview'] = ['preview.jpg']

    # Download any font zip files if provided
    download_font_files(submission['font_zip_url'], blueprint_subfolder)

    # Add creation time to Blueprint
    submission['blueprint']['created'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    # Write Blueprint as JSON
    blueprint_file = blueprint_subfolder / 'blueprint.json'
    with blueprint_file.open('w') as file_handle:
        json_dump(submission['blueprint'], file_handle, indent=2)
    print(f'Wrote Blueprint at blueprints/{letter}/{folder_name}/{blueprint.blueprint_number}/blueprint.json')


def _import_existing_blueprints():
    """
    Import any existing Blueprints and add them to the Database. This is
    purely a transition function, not intended for workflow execution.    
    """

    from json import load, dumps
    for series_folder in (Path(__file__).parent.parent / 'blueprints').glob('*/*'):
        for blueprint_folder in series_folder.glob('*'):
            if not blueprint_folder.is_dir():
                continue

            with (blueprint_folder / 'blueprint.json').open('r') as fh:
                blueprint = load(fh)

            series_name = series_folder.name.rsplit(' (', maxsplit=1)[0]
            series_year = int(series_folder.name[-5:-1])

            submission = parse_submission({
                'series_name': series_name,
                'series_year': series_year,
                'database_ids': '_No response_',
                'creator': blueprint['creator'],
                'description': '\n'.join(blueprint['description']),
                'blueprint': dumps(blueprint),
                'preview_url': '',
                'font_zip': '_No response_',
            })
            series, blueprint = create_new_blueprint(
                submission['series_name'], submission['series_year'],
                submission['database_ids'], submission['creator'],
                submission['description'], submission['blueprint'],
            )


# File is entrypoint
if __name__ == '__main__':
    parse_and_create_blueprint()

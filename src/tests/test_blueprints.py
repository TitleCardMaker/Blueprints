from json import load as json_load, JSONDecodeError
from pathlib import Path

from re import compile as re_compile, sub as re_sub, IGNORECASE
from typing import Iterator

from models.models import Blueprint


BLUEPRINT_FOLDER = Path(__file__).parent.parent.parent / 'blueprints'

# Non-tests

def read_blueprints() -> Iterator[tuple[Path, str, dict]]:
    for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
        blueprint_id = blueprint_file.parent
        series_subfolder = blueprint_file.parent.parent
        with blueprint_file.open('r') as file_handle:
            blueprint = json_load(file_handle)
            yield series_subfolder, blueprint_id, blueprint

    return None

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

    Args:
        series_name: Name of the Series.

    Returns:
        Tuple of the parent letter subfolder and the Path-safe name with
        prefix a/an/the and any illegal characters removed.
    """

    clean_name = str(series_name).translate(PATH_SAFE_TRANSLATION)
    sort_name = re_sub(r'^(a|an|the)(\s)', '', clean_name, flags=IGNORECASE)

    return sort_name[0].upper(), clean_name

# Tests

class TestFolderOrganization:
    def test_subfolder_names(self):
        for folder in BLUEPRINT_FOLDER.glob('*'):
            if folder.name != '.DS_Store':
                assert folder.name.upper() == folder.name, 'Folder Names Must Be Uppercase'

    def test_series_in_correct_subfolder(self):
        for series_folder in BLUEPRINT_FOLDER.glob('*/*'):
            if series_folder.name != '.DS_Store':
                letter, _ = get_blueprint_folders(series_folder.name)
                assert series_folder.parent.name == letter, 'Series must be placed in the correct letter subfolder'

    def test_series_folder_names(self):
        NAME_REGEX = re_compile(r'^.+\(\d{4}\)$')
        for series_folder in BLUEPRINT_FOLDER.glob('*/*'):
            if series_folder.name != '.DS_Store':
                assert NAME_REGEX.match(series_folder.name), 'Series Folder Names Must be Formatted as "Name (Year)"'

    def test_series_blueprint_folder_names(self):
        for folder in BLUEPRINT_FOLDER.glob('*/*/*'):
            # Skip Series blueprints.json and README
            if folder.is_file():
                continue

            assert folder.name.isdigit(), 'Series Blueprint subfolders must be named their blueprint ID'
            assert str(int(folder.name)) == folder.name, 'Series Blueprint subfolders must not be zero-padded'

    def test_series_subfolder_files(self):
        for file in BLUEPRINT_FOLDER.glob('*/*/*'):
            # Skip blueprint subfolder
            if file.is_dir():
                continue

            assert file.name in ('README.md', ), 'Only Series README files are allowed at root of the Series subfolder'


class TestBlueprintModels:
    def test_blueprint_is_valid_json(self):
        for file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
            content = None
            with file.open('r') as file_handle:
                try:
                    content = json_load(file_handle)
                except JSONDecodeError:
                    pass

            assert content is not None, 'All Blueprints must have an associated blueprint.json file'
            assert isinstance(content, dict), 'All blueprint files must have be a single Blueprint'

    def test_blueprint_is_valid_model(self):
        for _, _, blueprint in read_blueprints():
            assert Blueprint(**blueprint), blueprint


class TestBlueprintFiles:
    def test_blueprint_identifies_all_files(self):
        for series_subfolder, blueprint_id, blueprint in read_blueprints():
            # Get list of files in the blueprint subfolder
            given_files = {
                file.name
                for file in (series_subfolder / str(blueprint_id)).glob('*')
                if file.name != 'blueprint.json'
            }
            # Get all files listed in any Fonts
            font_files = {
                font['file']
                for font in blueprint.get('fonts', [])
                if font.get('file', None) is not None
            }
            previews = set(blueprint['previews'])
            assert len(given_files - font_files - previews) == 0, 'Only files listed in the blueprint can be included in the blueprint folder'
            assert len((font_files | previews) - given_files) == 0, 'All files listed in the blueprint must be included in the blueprint folder'

"""
Python script to be called by a GitHub action.

This script "lints" all blueprint.json files to standardize the JSON
across the project.
"""

from json import dump as json_dump, load as json_load, JSONDecodeError
from pathlib import Path


BLUEPRINT_FOLDER = Path(__file__).parent.parent.parent / 'blueprints'


def lint_blueprints() -> None:
    # Parse all Blueprints
    for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
        # Read this blueprint file
        with blueprint_file.open('r') as file_handle:
            # Parse JSON, skip if unable to parse
            try:
                blueprint = json_load(file_handle)
            except JSONDecodeError:
                continue

        # Rewrite blueprint to format it
        with blueprint_file.open('w') as file_handle:
            json_dump(blueprint, file_handle, indent=2)


if __name__ == '__main__':
    lint_blueprints()

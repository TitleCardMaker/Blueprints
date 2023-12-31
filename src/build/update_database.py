"""
Python script to be called by a GitHub action.

This script updates the Blueprint database with all Blueprint data.
"""


from datetime import datetime
from json import dumps, load as json_load, JSONDecodeError
from pathlib import Path

from src.database.db import db, Blueprint, Series
from src.build.helper import get_blueprint_folders


BLUEPRINT_FOLDER = Path(__file__).parent.parent.parent / 'blueprints'


def update_database() -> None:
    # Process each Blueprint file
    for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
        blueprint_number = int(blueprint_file.parent.name)
        series_path_name = blueprint_file.parent.parent.name

        # Find matching Series, skip if cannot be found
        series = db.query(Series).filter_by(path_name=series_path_name).first()
        if series is None:
            print(f'Cannot find Series "{series_path_name}" in Database')
            continue

        # Read this blueprint file
        with blueprint_file.open('r') as file_handle:
            # Parse JSON, skip if unable to parse
            try:
                blueprint_json = json_load(file_handle)
            except JSONDecodeError:
                continue

            # Find associated Blueprint
            blueprint = db.query(Blueprint)\
                .filter_by(series_id=series.id, blueprint_number=blueprint_number)\
                .first()
            if blueprint is None:
                print(f'Cannot find Blueprint[{series.name} ({series.year})][{blueprint_number}]')
                continue

            # Update Blueprint if it differs
            if blueprint.creator != blueprint_json['creator']:
                print(f'{"-" * 50}\nUpdating Creator of Blueprint[{series.name} ({series.year})][{blueprint_number}]\n')
                print(f'{blueprint.creator}\n\n{blueprint_json["creator"]}')
                blueprint.creator = blueprint_json['creator']
            if blueprint.created != (creation := datetime.strptime(blueprint_json['created'], '%Y-%m-%dT%H:%M:%S')):
                print(f'{"-" * 50}\nUpdating Created of Blueprint[{series.name} ({series.year})][{blueprint_number}]\n')
                print(f'{blueprint.created}\n\n{blueprint_json["created"]}')
                blueprint.created = creation
            if blueprint.json != (blueprint_string := dumps(blueprint_json)):
                print(f'{"-" * 50}\nUpdating JSON of Blueprint[{series.name} ({series.year})][{blueprint_number}]\n')
                print(f'{blueprint.json}\n\n{blueprint_string}')
                blueprint.json = dumps(blueprint_json)

    # Remove unmatched Blueprints from the database
    for blueprint in db.query(Blueprint).all():
        full_name = f'{blueprint.series.name} ({blueprint.series.year})'
        letter, _ = get_blueprint_folders(full_name)
        blueprint_file = BLUEPRINT_FOLDER \
            / str(letter) \
            / blueprint.series.path_name \
            / str(blueprint.blueprint_number)
        
        if not blueprint_file.exists():
            db.delete(blueprint)
            print(f'Deleting "{full_name})" Blueprint[{blueprint.blueprint_number}] - not found on file system')

    db.commit()


if __name__ == '__main__':
    update_database()

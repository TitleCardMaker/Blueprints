"""
Python script to be called by a GitHub action.

This serves as the entrypoint to all Blueprint actions.
"""

from argparse import ArgumentParser
from collections.abc import Callable
from sys import exit as sys_exit


ap = ArgumentParser()
ap.add_argument('--build-readme', action='store_true')
ap.add_argument('--lint-blueprints', action='store_true')
ap.add_argument('--notify-discord', action='store_true')
ap.add_argument('--parse-submission', action='store_true')
ap.add_argument('--parse-set-submission', action='store_true')
ap.add_argument('--resize-images', action='store_true')
ap.add_argument('--update-database', action='store_true')
ap.add_argument('--migrate-fields', action='store_true')

args = ap.parse_args()

# Functions to run
sequence: list[Callable[[], None]] = []

if args.parse_submission:
    from src.build.parse_submission import parse_and_create_blueprint
    sequence.append(parse_and_create_blueprint)

if args.parse_set_submission:
    from src.build.parse_submission import parse_blueprint_set
    sequence.append(parse_blueprint_set)

if args.lint_blueprints:
    from src.build.lint_blueprints import lint_blueprints
    sequence.append(lint_blueprints)

if args.migrate_fields:
    from src.build.update_database import migrate_season_titles_and_extras
    sequence.append(migrate_season_titles_and_extras)

if args.update_database:
    from src.build.update_database import update_database
    sequence.append(update_database)

if args.resize_images:
    from src.build.resize_images import resize_images
    sequence.append(resize_images)

if args.build_readme:
    from src.build.build_series_readme import build_series_readme
    from src.build.build_master_readme import build_master_readme
    sequence.append(build_series_readme)
    sequence.append(build_master_readme)

if args.notify_discord:
    from src.build.notify_discord import notify_discord
    sequence.append(notify_discord)

for function in sequence:
    try:
        function()
    except Exception as exc:
        print(f'Some error occured: {exc}')
        print('Exiting')
        sys_exit(1)

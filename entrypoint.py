

from argparse import ArgumentParser

ap = ArgumentParser()
ap.add_argument('--build-readme', action='store_true')
ap.add_argument('--lint-blueprints', action='store_true')
ap.add_argument('--notify-discord', action='store_true')
ap.add_argument('--parse-submission', action='store_true')
ap.add_argument('--resize-images', action='store_true')
ap.add_argument('--update-database', action='store_true')

args = ap.parse_args()

if args.parse_submission:
    from src.build.parse_submission import parse_and_create_blueprint
    parse_and_create_blueprint()

if args.lint_blueprints:
    from src.build.lint_blueprints import lint_blueprints
    lint_blueprints()

if args.update_database:
    from src.build.update_database import update_database
    update_database()

if args.resize_images:
    from src.build.resize_images import resize_images
    resize_images()

if args.build_readme:
    from src.build.build_series_readme import build_series_readme
    from src.build.build_master_readme import build_master_readme
    build_series_readme()
    build_master_readme()

if args.notify_discord:
    from src.build.notify_discord import notify_discord
    notify_discord()

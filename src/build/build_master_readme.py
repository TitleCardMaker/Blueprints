"""
Python script to be called by a GitHub action.

This script reads all Series blueprints.json files and writes summary
README's within each Series subfolder.
"""

from pathlib import Path

from src.database.db import db, Blueprint, Series, Set


README_TEMPLATE = """# TitleCardMaker Blueprints
[![Blueprint Validation](https://github.com/TitleCardMaker/Blueprints/actions/workflows/pytest.yml/badge.svg?branch=master)](https://github.com/TitleCardMaker/Blueprints/actions/workflows/pytest.yml)

Blueprints for importing premade Series configurations into TitleCardMaker.

---

## Blueprints

There are currently `{blueprint_count}` Blueprints available for `{series_count}` Series, submitted by `{creator_count}` Creators.

Series with the most Blueprints:
| Series | Blueprints |
| :--- | :--- |
| {series_name0} | {series_bp_count0} |
| {series_name1} | {series_bp_count1} |
| {series_name2} | {series_bp_count2} |
| {series_name3} | {series_bp_count3} |
| {series_name4} | {series_bp_count4} |

Creators with the most Blueprint Submissions:
| Username | Blueprints |
| :---: | :--- |
{creator_table}

## Sets

There are currently `{set_count}` Blueprint Sets available:

| Set ID | Name  | Linked Blueprints |
| :----: | :---: | :--- |
{set_table}
"""

USERNAME_ROW_TEMPLATE = '| {username} | {username_blueprint_count} |\n'
SET_ROW_TEMPLATE = '| `{set_id}` | {set_name} | {blueprints} |\n'


def build_master_readme() -> None:
    # Get top Series
    series_data: dict[str, int] = {}
    for blueprint in db.query(Blueprint).all():
        full_name = f'{blueprint.series.name} ({blueprint.series.year})'
        if full_name in series_data:
            series_data[full_name] += 1
        else:
            series_data[full_name] = 1
    top_series = sorted(series_data.items(), key=lambda item: item[1], reverse=True)

    # Get top usernames
    user_data: dict[str, int] = {}
    for blueprint in db.query(Blueprint).all():
        creators = map(str.strip, blueprint.creator.split(','))
        for creator in creators:
            if creator in user_data:
                user_data[creator] += 1
            else:
                user_data[creator] = 1
    top_users = sorted(user_data.items(), key=lambda item: item[1], reverse=True)

    # Add each user to table
    creator_table = ''
    for user in top_users:
        creator_table += USERNAME_ROW_TEMPLATE.format(
            username=user[0],
            username_blueprint_count=user[1],
        )

    # Add each Set to table
    set_table = ''
    for bp_set in db.query(Set).all():
        # Only show up to the first four Series in the set
        blueprint_str = '<br>'.join(
            f'{blueprint.series.name} [{blueprint.blueprint_number}]' for blueprint in bp_set.blueprints[:4]
        )
        if len(bp_set.blueprints) > 4:
            blueprint_str += f'<br>+{len(bp_set.blueprints)-4} more'

        set_table += SET_ROW_TEMPLATE.format(
            set_id=bp_set.id,
            set_name=bp_set.name,
            blueprints=blueprint_str,
        )

    # Generate counts
    data = {
        'blueprint_count': db.query(Blueprint).count(),
        'series_count': db.query(Series).count(),
        'creator_count': len(user_data),
        'set_count': db.query(Set).count(),
        'series_name0': top_series[0][0], 'series_bp_count0': top_series[0][1],
        'series_name1': top_series[1][0], 'series_bp_count1': top_series[1][1],
        'series_name2': top_series[2][0], 'series_bp_count2': top_series[2][1],
        'series_name3': top_series[3][0], 'series_bp_count3': top_series[3][1],
        'series_name4': top_series[4][0], 'series_bp_count4': top_series[4][1],
        'creator_table': creator_table, 'set_table': set_table,
    }

    # Format template with this data
    readme = README_TEMPLATE.format(**data)

    # Write README file
    readme_file = Path(__file__).parent.parent.parent / 'README.md'
    readme_file.write_text(readme)


if __name__ == '__main__':
    build_master_readme()

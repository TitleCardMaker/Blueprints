"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and then posts a message
on the Discord Webhook describing the created Blueprint.
"""


from datetime import datetime, timedelta
from os import environ
from tempfile import TemporaryFile

from discord_webhook import DiscordWebhook, DiscordEmbed
from requests import get

from src.build.parse_submission import parse_submission


DEFAULT_AVATAR_URL = (
    'https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/master/'
    '.github/logo.png'
)


def get_next_merge_time(time: datetime) -> datetime:
    nearest_4hr = time.replace(
        hour=time.hour // 4 * 4,
        minute=0, second=0, microsecond=0,
    )

    return nearest_4hr + timedelta(hours=4)


def format_timedelta(delta: timedelta) -> str:
    hours, seconds = divmod(delta.total_seconds(), 3600)
    minutes = int(seconds // 60)

    output = ''
    if (hours := int(hours)) > 0:
        output += f'{hours} hour{"s" if hours > 1 else ""}'

    if minutes > 0:
        if output:
            output += ', and '
        output += f'{minutes} minute{"s" if minutes > 1 else ""}'

    return output


def notify_discord() -> None:
    # Parse issue from environment variables
    # data = parse_submission()
    data={
        'series_name': 'Avatar the Last Airbender',
        'series_year': '2005',
        'database_ids': {'imdb': 'tt0417299'},
        'creator': 'CollinHeist',
        'preview_urls': [
            'https://github.com/CollinHeist/TCM-Blueprints-v2/assets/17693271/dc16e8a2-1a64-459a-aee8-695412eb7e47',
            'https://github.com/CollinHeist/TCM-Blueprints-v2/assets/17693271/46ff0741-9bb3-4e96-b92b-f2ae6dbc407d',
            'https://github.com/CollinHeist/TCM-Blueprints-v2/assets/17693271/8df64399-bb58-4047-877b-6240a785bf74'
        ],
        'font_zip_url': 'https://github.com/CollinHeist/TCM-Blueprints-v2/files/12841315/Archive.zip',
        'source_file_zip_url': 'https://github.com/CollinHeist/TCM-Blueprints-v2/files/12841316/Archive.2.zip',
        'blueprint': {
            'series': {
                'font_id': 0,
                'card_type': 'tinted frame',
                'episode_text_format': 'Chapter {episode_number}',
                'season_title_ranges': ['1', '2', '3'],
                'season_title_values': ['Book One: Water', 'Book Two: Earth', 'Book Three: Fire'],
                'extra_keys': [
                    'episode_text_font', 'episode_text_vertical_shift', 'episode_text_font_size', 'frame_width'
                ], 'extra_values': [
                    './fonts/Herculanum-Regular.ttf', '-8', '1.2', '5'
                ],
                'template_ids': [0]
            },
            'episodes': {
                's1e1': {'extra_keys': ['frame_color'], 'extra_values': ['rgb(67,150,205)']},
                's1e2': {'extra_keys': ['frame_color'], 'extra_values': ['rgb(67,150,205)']},
                's1e3': {'extra_keys': ['frame_color'], 'extra_values': ['rgb(67,150,205)']},
                's1e4': {'font_id': 1, 'extra_keys': ['frame_color'], 'extra_values': ['rgb(67,150,205)']}
            },
            'templates': [{'name': 'Test', 'card_type': 'calligraphy'}],
            'fonts': [
                {
                    'name': 'Avatar: The Last Airbender (Primary)',
                    'delete_missing': True,
                    'file': 'Avatar Airbender.ttf',
                    'size': 1.2,
                    'title_case':
                    'upper'
                },
                {
                    'name': 'Avatar: The Last Airbender (2)',
                    'delete_missing': True,
                    'file': 'Avatar Airbender2.ttf',
                    'size': 1.2,
                    'title_case': 'upper'
                }
            ],
            'creator': 'CollinHeist',
            'description': [
                'An example Blueprint featuring multiple preview files, source images, Fonts and Templates.',
                'The series name is input incorrectly as well.'
            ]
        }
    }

    # Create Embed object for webhook
    embed = DiscordEmbed(
        title=f'New Blueprint for {data["series_name"].strip()} ({data["series_year"]})',
        description=data['blueprint']['description'],
    )

    # Add creator as author
    embed.set_author(
        name=data['creator'],
        icon_url=environ.get('ISSUE_CREATOR_ICON_URL', DEFAULT_AVATAR_URL),
    )

    # Add preview
    embed.set_image(url=data['preview_urls'][0])

    # Add thumbnail if >1 preview
    if len(data['preview_urls']) > 1:
        embed.set_thumbnail(url=data['preview_urls'][1])
    
    # Add fields
    if (templates := len(data['blueprint'].get('templates', []))):
        embed.add_embed_field(name='Templates', value=templates)
    if (fonts := len(data['blueprint'].get('fonts', []))):
        embed.add_embed_field(name='Fonts', value=fonts)
    if (files := len(data['blueprint'].get('series', {}).get('source_files', []))):
        embed.add_embed_field(name='Source Files', value=files)

    # Add note about availability, add timestamp
    now = datetime.now()
    next_ = get_next_merge_time(now)
    embed.set_footer(f'This Blueprint will be available in {format_timedelta(next_-now)}')
    embed.set_timestamp()

    # Create Webhook for adding embeds
    webhook = DiscordWebhook(
        url=environ.get('DISCORD_WEBHOOK', 'https://discord.com/api/webhooks/1140417811072684103/IkoLb9iLGZqJ3-B5kARVaZjt43wA6Cs8PnFYHR0uPrnowP_mEdBi9ltgNEsfbxYUoHas'),
        username=environ.get('DISCORD_USERNAME', 'MakerBot'),
        avatar_url=environ.get('DISCORD_AVATAR', DEFAULT_AVATAR_URL)
    )

    # Add embed to Webhook, execute webhook
    webhook.add_embed(embed)
    webhook.execute()


if __name__ == '__main__':
    notify_discord()

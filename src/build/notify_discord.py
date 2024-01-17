"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and then posts a message
on the Discord Webhook describing the created Blueprint.
"""

from os import environ
from json import dumps, loads, JSONDecodeError
from pathlib import Path
from sys import exit as sys_exit

from discord_webhook import DiscordWebhook, DiscordEmbed

from src.build.parse_submission import download_zip, parse_submission


DEFAULT_AVATAR_URL = (
    'https://raw.githubusercontent.com/CollinHeist/static/main/logo.png'
)


def notify_discord() -> None:
    """
    Create and submit the Discord notification. This parses the
    Blueprint submission from the environment variables.
    """

    # Verify webhook URL is available
    if 'DISCORD_WEBHOOK' not in environ:
        print(f'DISCORD_WEBHOOK environment variable not provided')
        sys_exit(1)

    # Get issues
    try:
        issues = loads(environ.get('ISSUES'))
    except JSONDecodeError as exc:
        print(f'Unable to parse Issues as JSON')
        print(exc)
        print(environ.get('ISSUES'))
        sys_exit(1)

    # Get environment data
    for issue in issues:
        try:
            # Parse issue from this issue
            environment = {
                'ISSUE_BODY': dumps(issue['body']),
                'ISSUE_CREATOR': issue['user']['login'],
                'ISSUE_CREATOR_ICON_URL': issue['user']['avatar_url'],
            }
            data = parse_submission(environment=environment)

            # Shorten the description if longer than 200 characters
            description = '\n'.join(data['blueprint']['description'])
            if len(description) > 200:
                description = description[:200]
                if (index := description.rfind(' ')) > 0:
                    description = description[:index]
                description = f'{description} [...]'

            # Create Embed object for webhook
            embed = DiscordEmbed(
                title=f'New Blueprint for {data["series_name"].strip()} ({data["series_year"]})',
                description=description,
                color='6391d2'
            )

            # Add creator as author
            embed.set_author(
                name=data['creator'],
                icon_url=environment.get('ISSUE_CREATOR_ICON_URL', DEFAULT_AVATAR_URL),
            )

            # Add preview
            embed.set_image(url=data['preview_urls'][0])

            # Add thumbnail if >1 preview
            if len(data['preview_urls']) > 1:
                embed.set_thumbnail(url=data['preview_urls'][1])
            
            # Add fields
            if (templates := len(data['blueprint'].get('templates', []))):
                label = 'Templates' if templates > 1 else 'Template'
                embed.add_embed_field(label, templates)
            if (fonts := len(data['blueprint'].get('fonts', []))):
                label = 'Fonts' if fonts > 1 else 'Font'
                embed.add_embed_field(label, fonts)
            if (episodes := len(data['blueprint'].get('episodes', []))):
                label = 'Episodes' if episodes > 1 else 'Episode'
                embed.add_embed_field(label, episodes)
            if (zip_url := data['source_file_zip_url']):
                temp_dir = Path(__file__).parent / '.tmp'
                temp_dir.mkdir(parents=True, exist_ok=True)
                source_files = len(download_zip(zip_url, temp_dir))
                if source_files:
                    label = 'Source Files' if source_files > 1 else 'Source File'
                    embed.add_embed_field(label, source_files)

            # Add timestamp
            embed.set_timestamp()

            # Create Webhook for adding embeds
            webhook = DiscordWebhook(
                url=environ.get('DISCORD_WEBHOOK'),
                username=environ.get('DISCORD_USERNAME', 'MakerBot'),
                avatar_url=environ.get('DISCORD_AVATAR', DEFAULT_AVATAR_URL)
            )

            # Add embed to Webhook, execute webhook
            webhook.add_embed(embed)
            webhook.execute()
        except Exception as exc:
            print(f'Error notifying Issue - {exc}')


if __name__ == '__main__':
    notify_discord()

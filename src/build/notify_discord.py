"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and then posts a message
on the Discord Webhook describing the created Blueprint.
"""


from datetime import datetime, timedelta
from os import environ

from discord_webhook import DiscordWebhook, DiscordEmbed

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
    data = parse_submission()

    # Create Embed object for webhook
    embed = DiscordEmbed(
        title=f'New Blueprint Submission for {data["series_name"].strip()} ({data["series_year"]})',
        description=data['description'],
    )
    embed.set_author(
        name=data['creator'],
        icon_url=environ.get('ISSUE_CREATOR_ICON_URL', DEFAULT_AVATAR_URL),
    )
    embed.set_image(url=data['preview_url'])
    now = datetime.now()
    next_ = get_next_merge_time(now)
    embed.set_footer(f'This Blueprint will be available in {format_timedelta(next_-now)}')
    embed.set_timestamp()

    # Add embed object to webhook, execute webhook
    webhook = DiscordWebhook(
        url=environ.get('DISCORD_WEBHOOK'),
        username=environ.get('DISCORD_USERNAME', 'MakerBot'),
        avatar_url=environ.get('DISCORD_AVATAR', DEFAULT_AVATAR_URL)
    )
    webhook.add_embed(embed)
    webhook.execute()


if __name__ == '__main__':
    notify_discord()

"""
Python script to be called by a GitHub action.

This script resizes all preview images to a size of 1920x1080.
"""


from json import load as json_load, JSONDecodeError
from pathlib import Path

from imagesize import get as get_image_size
from PIL import Image


IMAGE_SIZE = (1920, 1080)

BLUEPRINT_FOLDER = Path(__file__).parent.parent.parent / 'blueprints'

REPO_URL = (
    'https://github.com/CollinHeist/TitleCardMaker-Blueprints/'
    'raw/master/blueprints'
)

def resize_images() -> None:
    for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
        # Read this blueprint file
        with blueprint_file.open('r') as file_handle:
            # Parse JSON, skip if unable to parse
            try:
                blueprint = json_load(file_handle)
            except JSONDecodeError:
                continue

            # Get this Blueprint's preview
            for preview_filename in blueprint['previews']:
                preview = blueprint_file.parent / preview_filename

                # Verify image is 1920x1080
                width, height = get_image_size(preview)
                if (width not in range(IMAGE_SIZE[0]-5, IMAGE_SIZE[0]+5)
                    or height not in range(IMAGE_SIZE[1]-5, IMAGE_SIZE[1]+5)):
                    # Open image; resize, convert to RGB (in case it was RGBA)
                    image = Image.open(preview).resize(IMAGE_SIZE).convert('RGB')
                    image.save(preview)
                    print(f'Resized "{preview}" to 1920x1080')


if __name__ == '__main__':
    resize_images()

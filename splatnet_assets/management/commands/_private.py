from io import BytesIO

import requests
from django.core.files import File

from splatnet_assets.models import Image


def get_latest_version():
    version_data_url = 'https://raw.githubusercontent.com/Leanny/leanny.github.io/master/splat3/versions.json'
    return requests.get(version_data_url).json()[-1]


def download_image(asset_type: str, asset_name: str, asset_url: str) -> Image:
    print(f'Downloading {asset_url}...')
    response = requests.get(asset_url)
    image_data = BytesIO(response.content)

    image, _created = Image.objects.get_or_create(type=asset_type, asset_name=asset_name)

    image.original_file_name = asset_url
    image.image = File(image_data, name=f'{asset_type}/{asset_url.split("/")[-1]}')

    image.save()

    return image


def download_image_from_path(asset_type: str, asset_name: str, asset_path: str) -> Image:
    prefix = 'https://raw.githubusercontent.com/Leanny/leanny.github.io/master/splat3/images/'
    return download_image(asset_type, asset_name, f'{prefix}{asset_path}')

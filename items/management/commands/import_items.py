import json

import requests
import jsonschema
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from items.models import Item


class Command(BaseCommand):
    BaseCommand.help = 'Import items from JSON data'

    json_item_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "image": {"type": "string"},
            "weight_grams": {"type": "integer"},
            "price": {"type": ["number", "string"]},
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--source',
            type=str,
            help='Choice source url with JSON data',
            default='https://raw.githubusercontent.com/stepik-a-w/drf-project-boxes/master/foodboxes.json')

    def validation_item(self, json_item):
        result = True
        try:
            jsonschema.validate(json_item, schema=self.json_item_schema)
        except jsonschema.exceptions.ValidationError as ex:
            print(ex)
            result = False
        return result

    def create_item(self, json_item):
        result = True
        response_image = requests.get(json_item['image'])
        if response_image:
            with NamedTemporaryFile() as img_temp:
                img_temp.write(response_image.content)
                filename = json_item['image'].split('/')[-1]
                try:
                    new_item = Item(
                        pk=json_item['id'],
                        title=json_item['title'],
                        description=json_item['description'],
                        image=File(img_temp, filename),
                        weight=json_item['weight_grams'],
                        price=json_item['price'],
                    )
                    new_item.save()
                except (TypeError, IntegrityError) as ex:
                    print(ex)
                    result = False
        else:
            print(f'Cannot download image from {json_item["image"]}')
            result = False
        return result

    def import_data(self, json_data):
        for json_item in json_data:
            if self.validation_item(json_item):
                print(f"Item id={json_item['id']} will be created")
                if Item.objects.filter(pk=json_item['id']).exists():
                    print('Item is exist. Created is cancelled')
                elif self.create_item(json_item):
                    print('Created is success')
                else:
                    print('Created is failed')
            else:
                print("JSON data of item isn't validation. Skipping creation")

    def handle(self, *args, **options):
        response = requests.get(options['source'])
        if response:
            try:
                json_data = response.json()
            except json.decoder.JSONDecodeError:
                print("The received data isn't JSON data")
                return
            self.import_data(json_data)
        else:
            print('An error has occurred')

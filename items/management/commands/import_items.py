import json

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.core.files import File
from django.core.files.temp import TemporaryFile
import requests
import jsonschema

from items.models import Item


class Command(BaseCommand):
    BaseCommand.help = 'Import items from JSON data'

    jitem_schema = {
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

    def validation_item(self, jitem):
        result = True
        try:
            jsonschema.validate(jitem, schema=self.jitem_schema)
        except jsonschema.exceptions.ValidationError as ex:
            print(ex)
            result = False
        return result

    def check_item_exists(self, jitem):
        try:
            Item.objects.get(pk=jitem['id'])
        except Item.DoesNotExist:
            return False
        return True

    def create_item(self, jitem):
        result = True
        response_image = requests.get(jitem['image'])
        if response_image:
            with TemporaryFile() as img_temp:
                img_temp.write(response_image.content)
                filename = jitem['image'].split('/')[-1]
                try:
                    new_item = Item(
                        pk=jitem['id'],
                        title=jitem['title'],
                        description=jitem['description'],
                        image=File(img_temp, filename),
                        weight=jitem['weight_grams'],
                        price=jitem['price'],
                    )
                    new_item.save()
                except (TypeError, IntegrityError) as ex:
                    print(ex)
                    result = False
        else:
            print(f'Cannot download image from {jitem["image"]}')
            result = False
        return result

    def import_data(self, jdata):
        for jitem in jdata:
            if self.validation_item(jitem):
                print(f"Item id={jitem['id']} will be created")
                if self.check_item_exists(jitem):
                    print('Item is exist. Created is cancelled')
                elif self.create_item(jitem):
                    print('Created is success')
                else:
                    print('Created is failed')
            else:
                print("JSON data of item isn't validation. Skipping creation")

    def handle(self, *args, **options):
        response = requests.get(options['source'])
        if response:
            try:
                jdata = response.json()
            except json.decoder.JSONDecodeError:
                print("The received data isn't JSON data")
                return
            self.import_data(jdata)
        else:
            print('An error has occurred')

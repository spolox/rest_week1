import json

import requests
import jsonschema
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from users.models import User

URL_DEFAULT_USERS = 'https://raw.githubusercontent.com/stepik-a-w/drf-project-boxes/master/recipients.json'


class Command(BaseCommand):
    BaseCommand.help = 'Import users from JSON data'

    json_user_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "email": {"type": "string"},
            "password": {"type": "string"},
            "info": {
                "type": "object",
                "properties": {
                    "surname": {"type": "string"},
                    "name": {"type": "string"},
                    "patronymic": {"type": "string"},
                },
            },
            "contacts": {
                "type": "object",
                "properties": {
                    "phoneNumber": {"type": "string"},
                },
            },
            "city_kladr": {"type": "string"},
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--source',
            type=str,
            help='Choice source url with JSON data',
            default=URL_DEFAULT_USERS)

    def validation_user(self, json_user):
        result = True
        try:
            jsonschema.validate(json_user, schema=self.json_user_schema)
        except jsonschema.exceptions.ValidationError as ex:
            print(ex)
            result = False
        return result

    def create_user(self, json_user):
        result = True
        username = json_user['email'].split('@')[0]
        try:
            new_user = User(
                pk=json_user['id'],
                username=username,
                email=json_user['email'],
                first_name=json_user['info']['name'],
                last_name=json_user['info']['surname'],
                middle_name=json_user['info']['patronymic'],
                phone=json_user['contacts']['phoneNumber'],
                address=json_user['city_kladr'],
            )
            new_user.set_password(json_user['password'])
            new_user.save()
        except (TypeError, IntegrityError) as ex:
            print(ex)
            result = False
        return result

    def import_data(self, json_data):
        for json_user in json_data:
            if self.validation_user(json_user):
                print(f"User id={json_user['id']} will be created")
                if User.objects.filter(pk=json_user['id']).exists():
                    print('User is exist. Created is cancelled')
                elif self.create_user(json_user):
                    print('Created is success')
                else:
                    print('Created is failed')
            else:
                print("JSON data of user isn't validation. Skipping creation")

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

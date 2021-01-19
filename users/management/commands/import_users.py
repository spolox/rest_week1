import json

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
import requests
import jsonschema

from users.models import User


class Command(BaseCommand):
    BaseCommand.help = 'Import users from JSON data'

    juser_schema = {
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
            default='https://raw.githubusercontent.com/stepik-a-w/drf-project-boxes/master/recipients.json')

    def validation_user(self, juser):
        result = True
        try:
            jsonschema.validate(juser, schema=self.juser_schema)
        except jsonschema.exceptions.ValidationError as ex:
            print(ex)
            result = False
        return result

    def check_user_exists(self, juser):
        try:
            User.objects.filter(pk=juser['id']).get()
        except User.DoesNotExist:
            return False
        return True

    def create_user(self, juser):
        result = True
        username = juser['email'].split('@')[0]
        try:
            new_user = User(
                pk=juser['id'],
                username=username,
                email=juser['email'],
                first_name=juser['info']['name'],
                last_name=juser['info']['surname'],
                middle_name=juser['info']['patronymic'],
                phone_number=juser['contacts']['phoneNumber'],
                address=juser['city_kladr'],
            )
            new_user.set_password(juser['password'])
            new_user.save()
        except (TypeError, IntegrityError) as ex:
            print(ex)
            result = False
        return result

    def import_data(self, jdata):
        for juser in jdata:
            if self.validation_user(juser):
                print(f"User id={juser['id']} will be created")
                if self.check_user_exists(juser):
                    print('User is exist. Created is cancelled')
                elif self.create_user(juser):
                    print('Created is success')
                else:
                    print('Created is failed')
            else:
                print("JSON data of user isn't validation. Skipping creation")

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

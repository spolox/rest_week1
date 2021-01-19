from datetime import datetime
import json

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.utils import timezone
import requests
import jsonschema

from reviews.models import Review
from users.models import User


class Command(BaseCommand):
    BaseCommand.help = 'Import items from JSON data'

    jreview_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "author": {"type": "integer"},
            "content": {"type": "string"},
            "created_at ": {"type": "string"},
            "published_at": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["id", "author", "content", "created_at ", "published_at", "status"],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--source',
            type=str,
            help='Choice source url with JSON data',
            default='https://raw.githubusercontent.com/stepik-a-w/drf-project-boxes/master/reviews.json')

    def validation_review(self, jreview):
        result = True
        try:
            jsonschema.validate(jreview, schema=self.jreview_schema)
        except jsonschema.exceptions.ValidationError as ex:
            print(ex)
            result = False
        return result

    def check_object_exists(self, model, pk):
        try:
            model.objects.get(pk=pk)
        except model.DoesNotExist:
            return False
        return True

    def get_time_created_at(self, created_at):
        return timezone.make_aware(datetime.strptime(created_at, '%Y-%m-%d'))

    def get_time_published_at(self, published_at):
        if published_at:
            result = timezone.make_aware(datetime.strptime(published_at, '%Y-%m-%d'))
        else:
            result = None
        return result

    def create_review(self, jreview):
        result = True
        if self.check_object_exists(User, jreview['author']):
            try:
                new_review = Review(
                    pk=jreview['id'],
                    author=User.objects.get(pk=jreview['author']),
                    text=jreview['content'],
                    created_at=self.get_time_created_at(jreview['created_at ']),
                    published_at=self.get_time_published_at(jreview['published_at']),
                    status=jreview['status'],
                )
                new_review.save()
            except (TypeError, IntegrityError) as ex:
                print(ex)
                result = False
        else:
            print(f"Author with id={jreview['author']} doesn't exist")
            result = False
        return result

    def import_data(self, jdata):
        for jreview in jdata:
            if self.validation_review(jreview):
                print(f"Review id={jreview['id']} will be created")
                if self.check_object_exists(Review, jreview['id']):
                    print('Review is exist. Created is cancelled')
                elif self.create_review(jreview):
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

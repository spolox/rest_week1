import json
from datetime import datetime

import requests
import jsonschema
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.utils import timezone

from reviews.models import Review
from users.models import User


class Command(BaseCommand):
    BaseCommand.help = 'Import items from JSON data'

    json_review_schema = {
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

    def validation_review(self, json_review):
        result = True
        try:
            jsonschema.validate(json_review, schema=self.json_review_schema)
        except jsonschema.exceptions.ValidationError as ex:
            print(ex)
            result = False
        return result

    def get_time_created_at(self, created_at):
        return timezone.make_aware(datetime.strptime(created_at, '%Y-%m-%d'))

    def get_time_published_at(self, published_at):
        if published_at:
            result = timezone.make_aware(datetime.strptime(published_at, '%Y-%m-%d'))
        else:
            result = None
        return result

    def create_review(self, json_review):
        result = True
        if User.objects.filter(pk=json_review['author']).exists():
            try:
                new_review = Review(
                    pk=json_review['id'],
                    author=User.objects.get(pk=json_review['author']),
                    text=json_review['content'],
                    created_at=self.get_time_created_at(json_review['created_at ']),
                    published_at=self.get_time_published_at(json_review['published_at']),
                    status=json_review['status'],
                )
                new_review.save()
            except (TypeError, IntegrityError) as ex:
                print(ex)
                result = False
        else:
            print(f"Author with id={json_review['author']} doesn't exist")
            result = False
        return result

    def import_data(self, json_data):
        for json_review in json_data:
            if self.validation_review(json_review):
                print(f"Review id={json_review['id']} will be created")
                if Review.objects.filter(pk=json_review['id']):
                    print('Review is exist. Created is cancelled')
                elif self.create_review(json_review):
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

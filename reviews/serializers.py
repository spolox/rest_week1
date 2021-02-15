from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.public_name', required=False)

    class Meta:
        model = Review
        fields = ['id', 'author', 'text', 'created_at', 'published_at', 'status']
        read_only_fields = ['id', 'author', 'created_at', 'published_at', 'status']
        extra_kwargs = {
            'text': {'required': True},
        }

    def create(self, validated_data):
        user = self.context['request'].user
        review = Review(
            author=user,
            text=validated_data['text'],
        )
        review.save()
        return review

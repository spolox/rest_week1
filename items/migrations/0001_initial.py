# Generated by Django 3.1.5 on 2021-01-22 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('image', models.ImageField(height_field='picture_height_field', upload_to='items', width_field='picture_width_field')),
                ('picture_height_field', models.PositiveIntegerField(default=0)),
                ('picture_width_field', models.PositiveIntegerField(default=0)),
                ('weight', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
            ],
        ),
    ]

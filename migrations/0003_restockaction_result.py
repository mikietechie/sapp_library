# Generated by Django 4.2.4 on 2023-09-09 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sapp_library', '0002_alter_book_created_by_alter_book_updated_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='restockaction',
            name='result',
            field=models.TextField(blank=True, editable=False, max_length=1024, null=True),
        ),
    ]
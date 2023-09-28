# Generated by Django 4.2.4 on 2023-09-10 19:12

from django.db import migrations, models
import sapp.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sapp_library', '0003_restockaction_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='genre',
            name='description',
            field=models.TextField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='genre',
            name='image',
            field=sapp.models.fields.ImageField(default=1, upload_to=''),
            preserve_default=False,
        ),
    ]
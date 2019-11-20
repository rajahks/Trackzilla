# Generated by Django 2.2.5 on 2019-11-10 16:15

from django.db import migrations
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

# TODO: Move this migration to the core app as this doesnot belong in the Users app.

def update_site_name(apps, schema_editor):
    SiteModel = apps.get_model('sites', 'Site')
    domain = settings.DOMAIN_NAME
    name = settings.DISPLAY_NAME

    SiteModel.objects.update_or_create(
        pk=settings.SITE_ID,
        defaults={ 'domain':domain, 'name':name}
    )

def delete_site_name(apps, schema_editor):
    SiteModel = apps.get_model('sites', 'Site')
    try:
        SiteModel.objects.get(id=settings.SITE_ID).delete()

    except SiteModel.DoesNotExist:
        logger.warning("Trying to delete site %d which doesnot exist"%(settings.SITE_ID,))

class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0001_initial'),
        ('sites', '0002_alter_domain_unique'), # Required to reference `sites` in `apps.get_model()`
    ]

    operations = [
        migrations.RunPython(update_site_name,delete_site_name),
    ]

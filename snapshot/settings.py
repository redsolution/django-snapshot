# -*- coding: utf-8 -*-
from django.conf import settings as project_settings
from os.path import join, dirname

SNAPSHOTS_DIR = getattr(project_settings, 'SNAPSHOTS_DIR',
    join(dirname(project_settings.MEDIA_ROOT), 'snapshots'))

SNAPSHOT_TARGETS = getattr(project_settings, 'SNAPSHOT_TARGETS', [
    'snapshot.models.MediaUploadDirectory',
    'snapshot.models.PostgresDatabase',
])

# -*- coding: utf-8 -*-
from django.conf import settings as project_settings
from os.path import join, dirname

SNAPSHOTS_DIR = getattr(project_settings, 'SNAPSHOTS_DIR',
    join(dirname(project_settings.MEDIA_ROOT), 'snapshots'))

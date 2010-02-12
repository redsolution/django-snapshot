# -*- coding: utf-8 -*-
from optparse import OptionParser
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from snapshot.models import SnapSite

class Command(BaseCommand):
    help = '''TODO: Usage description
    '''

    def handle(self, *args, **options):
        if args:
            action = args[0]
        else:
            action = None

        # TODO: check settings directory
        if action == 'save':
            site = SnapSite(settings)

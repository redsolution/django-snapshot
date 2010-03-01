# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import OptionParser
from snapshot.models import SnapSite
from snapshot import settings as snapshot_settings
import os

class Command(BaseCommand):
    help = '''Usage:
    snap save         - take a snapshot at current time
    snap restore [i]  - restore from [i] snapshot (0 by default)
    snap list         - list all available snapshots
    '''

    def handle(self, *args, **options):
        if args:
            action = args[0]
        else:
            action = None

        # TODO: check settings directory
        if action == 'save':
            site = SnapSite(settings)
            site.snapshot()
        elif action == 'restore':
            if len(args) > 1:
                try:
                    number = int(args[1])
                except ValueError:
                    raise CommandError('restre second argument must be digit')
            else:
                number = 0

            try:
                snapshots = os.listdir(snapshot_settings.SNAPSHOTS_DIR)
                snapshots = sorted(snapshots, reverse=True)
                snapshot_filename = snapshots[number]
            except IndexError:
                raise CommandError('Incorrect snapshot number')
            except OSError:
                raise CommandError("Snapshots wasn't created")

            site = SnapSite(settings)
            site.restore(snapshot_filename)
        elif action == 'list':
            try:
                snapshots = os.listdir(snapshot_settings.SNAPSHOTS_DIR)
                snapshots = sorted(snapshots, reverse=True)
            except OSError:
                raise CommandError("Snapshots wasn't created")
            for i in range(len(snapshots)):
                print '%d: %s' % (i, snapshots[i])
        else:
            print self.help

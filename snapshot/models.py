# -*- coding: utf-8 -*-
import os
import sys
from optparse import OptionParser
from subprocess import Popen, PIPE
import datetime
import logging
import shutil
from snapshot import settings
from django.utils import simplejson

logging.getLogger().setLevel(logging.DEBUG)


class MustOverride(Exception):
    pass

class BackupTarget(object):
    '''Class for main  targets to backup and restore
    It supposed to be overriden by database and filesystem extensions
    '''
    name = 'backup_target'
    dump_file = None

    def snapshot(self):
        raise MustOverride

    def restore(self, dump):
        raise MustOverride

    def save_settings(self):
        '''
        Return JSON string with target name and target dump file
        '''
        return {
            'name': self.name,
            'dump_file': self.dump_file,
        }

    def load_settings(self, json_string):
        '''
        Load data from JSON string
        '''
        json = simplejson.loads(json_string)
        for item in json:
            if item.get('name') == self.name:
                self.dump_file = item.get('dump_file')

#===============================================================================
# Database snapshots
#===============================================================================

class Database(BackupTarget):
    '''Database snapshot representation'''
    connection_settings = {
        'dbname': None,
        'host': None,
        'port': None,
        'user': None,
        'password': None,
    }
    encoding = 'UTF-8'

    def __init__(self, settings_module):
        self.connection_settings['dbname'] = getattr(settings_module, 'DATABASE_NAME')
        self.connection_settings['host'] = getattr(settings_module, 'DATABASE_HOST', '127.0.0.1')
        self.connection_settings['port'] = getattr(settings_module, 'DATABASE_PORT')
        self.connection_settings['user'] = getattr(settings_module, 'DATABASE_USER')
        self.connection_settings['password'] = getattr(settings_module, 'DATABASE_PASSWORD')
        return super(Database, self).__init__()


class PostgresDatabase(Database):
    name = 'postgres'

    def _re_create_database(self):
        return '\n'.join([
            '\connect postgres;',
            'DROP DATABASE %s;' % self.connection_settings['dbname'],
            "CREATE DATABASE %s WITH OWNER %s ENCODING='%s';" % (
                self.connection_settings['dbname'],
                self.connection_settings['user'],
                self.encoding,
            ),
            '\connect %s;' % self.connection_settings['dbname'],
            '',
        ])

    def _authenticate(self):
        if 'user' in self.connection_settings:
            os.environ['PGUSER'] = self.connection_settings['user']
        if 'password' in self.connection_settings:
            os.environ['PGPASSWORD'] = self.connection_settings['password']
        if 'dbname' in self.connection_settings:
            os.environ['PGDATABASE'] = self.connection_settings['dbname']

    def snapshot(self):
        '''Make a snapshot of database. File in sql format supposed to be written on disk'''
        logging.info('Taking a snapshot')
        args = []
        self._authenticate()
        if 'host' in self.connection_settings:
            args += ['--host=%s' % self.connection_settings['host']]
        if 'port' in self.connection_settings:
            args += ['--port=%s' % self.connection_settings['port']]
        if self.connection_settings['dbname']:
            args += [self.connection_settings['dbname']]

        command = 'pg_dump %s' % (' '.join(args))

        pipe = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
        (stdout, stderr) = pipe.communicate(self.connection_settings['password'])

        if pipe.wait() != 0:
            logging.error('Error in snapshot')
        else:
            logging.info('Snapshot finished')
            self.dump_file = 'database_postgres_backup.%s.sql' % (
                datetime.datetime.now().strftime('%Y-%m-%d_%H-%M'))
            file = open(os.path.join(settings.SNAPSHOTS_DIR, self.dump_file), 'w')

            # save dump to file
            file.write(self._re_create_database())
            file.write(stdout)
            file.close()

    def restore(self):
        '''Restore from sql file. Filename should be provided in self.dump_file'''
        if not self.dump_file:
            logging.error('Restore filename is None. Aborting')
            return

        logging.info('Restoring from %s' % self.dump_file)
        args = []
        self._authenticate()
        if 'host' in self.connection_settings:
            args += ['--host=%s' % self.connection_settings['host']]
        if 'port' in self.connection_settings:
            args += ['--port=%s' % self.connection_settings['port']]

        command = 'psql %s < %s' % (' '.join(args), os.path.join(
            settings.SNAPSHOTS_DIR, self.dump_file))

        pipe = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)

        if pipe.wait() != 0:
            logging.error('Error while restoring')
        else:
            logging.info('Restored successfully')

#===============================================================================
# Directory snapshots
#===============================================================================

class Directory(BackupTarget):
    '''File directory backup target'''
    # TODO: filemask = ''
    backup_dir = None

    def __init__(self, backup_dir):
        self.backup_dir = backup_dir
        return super(Directory, self).__init__()

    def snapshot(self):
        logging.info('Taking a snapshot')

        self.dump_file = 'directory_backup.%s.tar' % (
            datetime.datetime.now().strftime('%Y-%m-%d_%H-%M'))

        command = 'tar cf %s -C %s .' % (os.path.join(
            settings.SNAPSHOTS_DIR, self.dump_file), self.backup_dir)
        pipe = Popen(command, shell=True)

        if pipe.wait() != 0:
            logging.error('Error while snapshot')
        else:
            logging.info('Snapshot successfully')

    def restore(self):
        if not self.dump_file:
            logging.error('Restore filename is None. Aborting')
            return

        logging.info('Restoring from %s' % self.dump_file)

        command = 'tar xf %s -C %s .' % (os.path.join(
            settings.SNAPSHOTS_DIR, self.dump_file), self.backup_dir)

        pipe = Popen(command, shell=True)
        if pipe.wait() != 0:
            logging.error('Error while restoring')
        else:
            logging.info('Restored successfully')

class MediaDirectory(Directory):
    name = 'media'
    def __init__(self, settings_module):
        return super(MediaDirectory, self).__init__(settings_module.MEDIA_ROOT)

#===============================================================================
# Collating objects class
#===============================================================================

class SnapSite(object):
    '''A Django site snapshot

    Attributes:

        media - path to media directory
        database - dictionary with database settings
        settings - imported settings module from the site
    '''
    settings = None
    media = None
    database = None

    def __init__(self, settings=None):
        if settings:
            self.settings = settings
        else:
            from django.conf import settings
        self.media = MediaDirectory(settings)
        self.database = PostgresDatabase(settings)
        return super(SnapSite, self).__init__()

    def snapshot(self):
        self.database.snapshot()
        self.media.snapshot()

        # save settings to file
        json_file = open(os.path.join(settings.SNAPSHOTS_DIR, 'info.json'), 'w')
        json_file.write(simplejson.dumps(
            [self.database.save_settings(), self.media.save_settings()],
            indent=4,
        ))
        json_file.close()
        
        # and gzip contents to snapshot
        archive_name = 'snapshot.%s.tar.gz' % (datetime.datetime.now().strftime('%Y-%m-%d_%H-%M'))

        command = 'tar czf %(archive_name)s --remove-files -C %(path)s %(files)s ' % ({
            'archive_name': os.path.join(settings.SNAPSHOTS_DIR, archive_name),
            'path': settings.SNAPSHOTS_DIR,
            'files': ' '.join([self.database.dump_file, self.media.dump_file, 'info.json']),
        })

        pipe = Popen(command, shell=True)
        if pipe.wait() != 0:
            logging.error('Error while restoring')
        else:
            logging.info('Snapshot successfully')


===============
django-snapshot
===============

Installation:
=============

1. Add ``snapshot`` to ``INSTALLED_APPS`` in your ``settings.py`` within your django project.


Usage
======

Use management command ``snap``

    ``./manage.py snap``

*help:*

*    snap save         - take a snapshot at current time
*    snap restore [i]  - restore from [i] snapshot (0 by default)
*    snap list         - list all available snapshots
 

How it works:
=============

Program create \*.tar.gz archive with files:

    **info.json** - JSON description of archive's contents for ``restore`` command
    
    **directory_backup.2011-01-01.tar** - backup of upload directory
    
    **database_postgres_backup.2011-01-01.sql** - SQL database dump

All files created and restored automatically, you do not need to bother of 
their structure.

Restrictions:
==============

Django-snapshot works now only with PostgreSQL database. Nor sqlite or MySQL are not supported.
If you have any suggestions, email developers. Any feedback is welcome.
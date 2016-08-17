#!/usr/bin/env python
import os
import sys
import django
import Bcfg2.Options
import Bcfg2.DBSettings

try:
    import Bcfg2.Server.models
except ImportError:
    pass

parser = Bcfg2.Options.get_parser()
parser.add_options([Bcfg2.Options.PositionalArgument('django_command', nargs='*')])
parser.parse()

if django.VERSION[0] == 1 and django.VERSION[1] <= 6:
    try:
        imp.find_module('settings') # Assumed to be in the same directory.
    except ImportError:
        import sys
        sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
        sys.exit(1)

if __name__ == "__main__":
    if django.VERSION[0] == 1 and django.VERSION[1] >= 6:
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv[:1] + Bcfg2.Options.setup.django_command)
    else:
        execute_manager(settings)

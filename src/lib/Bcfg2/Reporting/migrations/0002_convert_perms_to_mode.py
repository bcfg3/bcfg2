# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Reporting', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fileperms',
            old_name='perms',
            new_name='mode',
        ),
        migrations.AlterUniqueTogether(
            name='fileperms',
            unique_together=set([('owner', 'group', 'mode')]),
        ),
    ]

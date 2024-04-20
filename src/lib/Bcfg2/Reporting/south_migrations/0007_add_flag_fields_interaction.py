# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Interaction.dry_run'
        db.add_column('Reporting_interaction', 'dry_run',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Interaction.only_important'
        db.add_column('Reporting_interaction', 'only_important',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Interaction.dry_run'
        db.delete_column('Reporting_interaction', 'dry_run')

        # Deleting field 'Interaction.only_important'
        db.delete_column('Reporting_interaction', 'only_important')


    models = {
        'Reporting.actionentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'ActionEntry'},
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'output': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'check'", 'max_length': '128'})
        },
        'Reporting.bundle': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Bundle'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'Reporting.client': {
            'Meta': {'object_name': 'Client'},
            'creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_interaction': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_client'", 'on_delete': 'models.CASCADE', 'null': 'True', 'to': "orm['Reporting.Interaction']"}),
            'expiration': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'Reporting.deviceentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'DeviceEntry', '_ormbases': ['Reporting.PathEntry']},
            'current_major': ('django.db.models.fields.IntegerField', [], {}),
            'current_minor': ('django.db.models.fields.IntegerField', [], {}),
            'device_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'pathentry_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['Reporting.PathEntry']", 'unique': 'True', 'on_delete': 'models.CASCADE', 'primary_key': 'True'}),
            'target_major': ('django.db.models.fields.IntegerField', [], {}),
            'target_minor': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.failureentry': {
            'Meta': {'object_name': 'FailureEntry'},
            'entry_type': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'})
        },
        'Reporting.fileacl': {
            'Meta': {'object_name': 'FileAcl'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'})
        },
        'Reporting.fileperms': {
            'Meta': {'unique_together': "(('owner', 'group', 'mode'),)", 'object_name': 'FilePerms'},
            'group': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'owner': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'Reporting.group': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Group'},
            'bundles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.Bundle']", 'symmetrical': 'False'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'profile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'Reporting.interaction': {
            'Meta': {'ordering': "['-timestamp']", 'unique_together': "(('client', 'timestamp'),)", 'object_name': 'Interaction'},
            'actions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.ActionEntry']", 'symmetrical': 'False'}),
            'bad_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'bundles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.Bundle']", 'symmetrical': 'False'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'interactions'", 'on_delete': 'models.CASCADE', 'to': "orm['Reporting.Client']"}),
            'dry_run': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'extra_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'failures': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.FailureEntry']", 'symmetrical': 'False'}),
            'good_count': ('django.db.models.fields.IntegerField', [], {}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'only_important': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'packages': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.PackageEntry']", 'symmetrical': 'False'}),
            'paths': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.PathEntry']", 'symmetrical': 'False'}),
            'posixgroups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.POSIXGroupEntry']", 'symmetrical': 'False'}),
            'posixusers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.POSIXUserEntry']", 'symmetrical': 'False'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'on_delete': 'models.CASCADE', 'null': 'True', 'to': "orm['Reporting.Group']"}),
            'repo_rev_code': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'sebooleans': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SEBooleanEntry']", 'symmetrical': 'False'}),
            'sefcontexts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SEFcontextEntry']", 'symmetrical': 'False'}),
            'seinterfaces': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SEInterfaceEntry']", 'symmetrical': 'False'}),
            'selogins': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SELoginEntry']", 'symmetrical': 'False'}),
            'semodules': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SEModuleEntry']", 'symmetrical': 'False'}),
            'senodes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SENodeEntry']", 'symmetrical': 'False'}),
            'sepermissives': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SEPermissiveEntry']", 'symmetrical': 'False'}),
            'seports': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SEPortEntry']", 'symmetrical': 'False'}),
            'server': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'services': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.ServiceEntry']", 'symmetrical': 'False'}),
            'seusers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.SEUserEntry']", 'symmetrical': 'False'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'total_count': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.linkentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'LinkEntry', '_ormbases': ['Reporting.PathEntry']},
            'current_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'pathentry_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['Reporting.PathEntry']", 'unique': 'True', 'on_delete': 'models.CASCADE', 'primary_key': 'True'}),
            'target_path': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'Reporting.packageentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'PackageEntry'},
            'current_version': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {}),
            'target_version': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'verification_details': ('django.db.models.fields.TextField', [], {'default': "''"})
        },
        'Reporting.pathentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'PathEntry'},
            'acls': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['Reporting.FileAcl']", 'symmetrical': 'False'}),
            'current_perms': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'on_delete': 'models.CASCADE', 'to': "orm['Reporting.FilePerms']"}),
            'detail_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'details': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'path_type': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state': ('django.db.models.fields.IntegerField', [], {}),
            'target_perms': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'on_delete': 'models.CASCADE', 'to': "orm['Reporting.FilePerms']"})
        },
        'Reporting.performance': {
            'Meta': {'object_name': 'Performance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interaction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'performance_items'", 'on_delete': 'models.CASCADE', 'to': "orm['Reporting.Interaction']"}),
            'metric': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '32', 'decimal_places': '16'})
        },
        'Reporting.posixgroupentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'POSIXGroupEntry'},
            'current_gid': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'gid': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.posixuserentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'POSIXUserEntry'},
            'current_gecos': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'current_group': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'current_home': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'current_shell': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'current_uid': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'gecos': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'home': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'shell': ('django.db.models.fields.CharField', [], {'default': "'/bin/bash'", 'max_length': '1024'}),
            'state': ('django.db.models.fields.IntegerField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'Reporting.sebooleanentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SEBooleanEntry'},
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {}),
            'value': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'Reporting.sefcontextentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SEFcontextEntry'},
            'current_selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'filetype': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.seinterfaceentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SEInterfaceEntry'},
            'current_selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.seloginentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SELoginEntry'},
            'current_selinuxuser': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'selinuxuser': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.semoduleentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SEModuleEntry'},
            'current_disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.senodeentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SENodeEntry'},
            'current_selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'proto': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.sepermissiveentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SEPermissiveEntry'},
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.seportentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SEPortEntry'},
            'current_selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'selinuxtype': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        },
        'Reporting.serviceentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'ServiceEntry'},
            'current_status': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {}),
            'target_status': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128'})
        },
        'Reporting.seuserentry': {
            'Meta': {'ordering': "('state', 'name')", 'object_name': 'SEUserEntry'},
            'current_prefix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'current_roles': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'exists': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hash_key': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'roles': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'state': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['Reporting']
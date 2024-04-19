""" Verify attributes for configuration entries that cannot be
verified with an XML schema alone. """

import os
import re
import Bcfg2.Server.Lint
import Bcfg2.Client.Tools.VCS
from Bcfg2.Server.Plugins.Packages import Apt, Yum
from Bcfg2.Client.Tools.POSIX.base import device_map


# format verifying functions.  TODO: These should be moved into XML
# schemas where possible.
def is_filename(val):
    """ Return True if val is a string describing a valid full path
    """
    return val.startswith("/") and len(val) > 1


def is_selinux_type(val):
    """ Return True if val is a string describing a valid (although
    not necessarily existent) SELinux type """
    return re.match(r'^[a-z_]+_t', val)


def is_selinux_user(val):
    """ Return True if val is a string describing a valid (although
    not necessarily existent) SELinux user """
    return re.match(r'^[a-z_]+_u', val)


def is_octal_mode(val):
    """ Return True if val is a string describing a valid octal
    permissions mode """
    return re.match(r'[0-7]{3,4}', val)


def is_username(val):
    """ Return True if val is a string giving either a positive
    integer uid, or a valid Unix username """
    return re.match(r'^([A-z][-_A-z0-9]{0,30}|\d+)$', val)


def is_device_mode(val):
    """ Return True if val is a string describing a positive integer
    """
    return re.match(r'^\d+$', val)


def is_vcs_type(val):
    """ Return True if val is a supported vcs type handled by the
    current client tool """
    return (val != 'Path' and
            hasattr(Bcfg2.Client.Tools.VCS.VCS, 'Install%s' % val))


class RequiredAttrs(Bcfg2.Server.Lint.ServerPlugin):
    """ Verify attributes for configuration entries that cannot be
    verified with an XML schema alone. """
    def __init__(self, *args, **kwargs):
        Bcfg2.Server.Lint.ServerPlugin.__init__(self, *args, **kwargs)
        self.required_attrs = {
            'Path': {
                '__any__': {'name': is_filename},
                'augeas': {'owner': is_username, 'group': is_username,
                           'mode': is_octal_mode},
                'device': {'owner': is_username, 'group': is_username,
                           'mode': is_octal_mode,
                           'dev_type': lambda v: v in device_map},
                'directory': {'owner': is_username, 'group': is_username,
                              'mode': is_octal_mode},
                'file': {'owner': is_username, 'group': is_username,
                         'mode': is_octal_mode, '__text__': None},
                'hardlink': {'owner': is_username, 'group': is_username,
                             'mode': is_octal_mode, 'to': is_filename},
                'symlink': {},
                'ignore': {},
                'nonexistent': {},
                'permissions': {'owner': is_username, 'group': is_username,
                                'mode': is_octal_mode},
                'vcs': {'vcstype': is_vcs_type, 'revision': None,
                        'sourceurl': None},
            },
            'Service': {
                '__any__': {'name': None},
                'smf': {'name': None, 'FMRI': None}
            },
            'Action': {
                None: {
                    'name': None,
                    'timing': lambda v: v in ['pre', 'post', 'both'],
                    'when': lambda v: v in ['modified', 'always'],
                    'status': lambda v: v in ['ignore', 'check'],
                    'command': None,
                },
            },
            'ACL': {
                'default': {
                    'scope': lambda v: v in ['user', 'group'],
                    'perms': lambda v: re.match(r'^([0-7]|[rwx\-]{0,3}', v),
                },
                'access': {
                    'scope': lambda v: v in ['user', 'group'],
                    'perms': lambda v: re.match(r'^([0-7]|[rwx\-]{0,3}', v),
                },
                'mask': {
                    'perms': lambda v: re.match(r'^([0-7]|[rwx\-]{0,3}', v),
                },
            },
            'Package': {
                '__any__': {'name': None},
            },
            'SEBoolean': {
                None: {
                    'name': None,
                    'value': lambda v: v in ['on', 'off'],
                },
            },
            'SEModule': {
                None: {'name': None, '__text__': None},
            },
            'SEPort': {
                None: {
                    'name': lambda v: re.match(r'^\d+(-\d+)?/(tcp|udp)', v),
                    'selinuxtype': is_selinux_type,
                },
            },
            'SEFcontext': {
                None: {'name': None, 'selinuxtype': is_selinux_type},
            },
            'SENode': {
                None: {
                    'name': lambda v: "/" in v,
                    'selinuxtype': is_selinux_type,
                    'proto': lambda v: v in ['ipv6', 'ipv4']
                },
            },
            'SELogin': {
                None: {'name': is_username, 'selinuxuser': is_selinux_user},
            },
            'SEUser': {
                None: {
                    'name': is_selinux_user,
                    'roles': lambda v: all(is_selinux_user(u)
                                           for u in " ".split(v)),
                    'prefix': None,
                },
            },
            'SEInterface': {
                None: {'name': None, 'selinuxtype': is_selinux_type},
            },
            'SEPermissive': {
                None: {'name': is_selinux_type},
            },
            'POSIXGroup': {
                None: {'name': is_username},
            },
            'POSIXUser': {
                None: {'name': is_username},
            },
        }

    def Run(self):
        self.check_packages()
        if "Defaults" in self.core.plugins:
            self.logger.info("Defaults plugin enabled; skipping required "
                             "attribute checks")
        else:
            self.check_rules()
            self.check_bundles()

    @classmethod
    def Errors(cls):
        return {"missing-elements": "error",
                "unknown-entry-type": "error",
                "unknown-entry-tag": "error",
                "required-attrs-missing": "error",
                "required-attr-format": "error",
                "extra-attrs": "warning"}

    def check_default_acl(self, path):
        """ Check that a default ACL contains either no entries or minimum
        required entries """
        defaults = 0
        if path.xpath("ACL[@type='default' and @scope='user' and @user='']"):
            defaults += 1
        if path.xpath("ACL[@type='default' and @scope='group' and @group='']"):
            defaults += 1
        if path.xpath("ACL[@type='default' and @scope='other']"):
            defaults += 1
        if defaults > 0 and defaults < 3:
            self.LintError(
                "missing-elements",
                "A Path must have either no default ACLs or at"
                " least default:user::, default:group:: and"
                " default:other::")

    def check_packages(self):
        """ Check Packages sources for Source entries with missing
        attributes. """
        if 'Packages' not in self.core.plugins:
            return

        for source in self.core.plugins['Packages'].sources:
            if isinstance(source, Yum.YumSource):
                if (not source.pulp_id and not source.url and
                        not source.rawurl):
                    self.LintError(
                        "required-attrs-missing",
                        "A %s source must have either a url, rawurl, or "
                        "pulp_id attribute: %s" %
                        (source.ptype, self.RenderXML(source.xsource)))
            elif not source.url and not source.rawurl:
                self.LintError(
                    "required-attrs-missing",
                    "A %s source must have either a url or rawurl attribute: "
                    "%s" %
                    (source.ptype, self.RenderXML(source.xsource)))

            if (not isinstance(source, Apt.AptSource) and
                    source.recommended):
                self.LintError(
                    "extra-attrs",
                    "The recommended attribute is not supported on %s sources:"
                    " %s" %
                    (source.ptype, self.RenderXML(source.xsource)))

    def check_rules(self):
        """ check Rules for Path entries with missing attrs """
        if 'Rules' not in self.core.plugins:
            return

        for rules in list(self.core.plugins['Rules'].entries.values()):
            xdata = rules.pnode.data
            for path in xdata.xpath("//Path"):
                self.check_entry(path,
                                 os.path.join(Bcfg2.Options.setup.repository,
                                              rules.name))

    def check_bundles(self):
        """ Check bundles for BoundPath and BoundPackage entries with missing
        attrs. """
        if 'Bundler' not in self.core.plugins:
            return

        for bundle in list(self.core.plugins['Bundler'].entries.values()):
            if self.HandlesFile(bundle.name) and bundle.template is None:
                for path in bundle.xdata.xpath(
                        "//*[substring(name(), 1, 5) = 'Bound']"):
                    self.check_entry(path, bundle.name)

                # ensure that abstract Path tags have either name
                # or glob specified
                for path in bundle.xdata.xpath("//Path"):
                    if ('name' not in path.attrib and
                        'glob' not in path.attrib):
                        self.LintError(
                            "required-attrs-missing",
                            "Path tags require either a 'name' or 'glob' "
                            "attribute: \n%s" % self.RenderXML(path))
                # ensure that abstract Package tags have either name
                # or group specified
                for package in bundle.xdata.xpath("//Package"):
                    if ('name' not in package.attrib and
                        'group' not in package.attrib):
                        self.LintError(
                            "required-attrs-missing",
                            "Package tags require either a 'name' or 'group' "
                            "attribute: \n%s" % self.RenderXML(package))

    def check_entry(self, entry, filename):
        """ Generic entry check.

        :param entry: The XML entry to check for missing attributes.
        :type entry: lxml.etree._Element
        :param filename: The filename the entry came from
        :type filename: string
        """
        if self.HandlesFile(filename):
            name = entry.get('name')
            tag = entry.tag
            if tag.startswith("Bound"):
                tag = tag[5:]
            if tag not in self.required_attrs:
                self.LintError("unknown-entry-tag",
                               "Unknown entry tag '%s': %s" %
                               (tag, self.RenderXML(entry)))
                return

            etype = entry.get('type')
            if etype in self.required_attrs[tag]:
                required_attrs = self.required_attrs[tag][etype]
            elif '__any__' in self.required_attrs[tag]:
                required_attrs = self.required_attrs[tag]['__any__']
            else:
                self.LintError("unknown-entry-type",
                               "Unknown %s type %s: %s" %
                               (tag, etype, self.RenderXML(entry)))
                return
            attrs = set(entry.attrib.keys())

            if 'dev_type' in required_attrs:
                dev_type = entry.get('dev_type')
                if dev_type in ['block', 'char']:
                    # check if major/minor are specified
                    required_attrs['major'] = is_device_mode
                    required_attrs['minor'] = is_device_mode

            if tag == 'Path':
                self.check_default_acl(entry)

            if tag == 'ACL' and 'scope' in required_attrs:
                required_attrs[entry.get('scope')] = is_username

            if '__text__' in required_attrs:
                fmt = required_attrs['__text__']
                del required_attrs['__text__']
                if (not entry.text and
                        not entry.get('empty', 'false').lower() == 'true'):
                    self.LintError("required-attrs-missing",
                                   "Text missing for %s %s in %s: %s" %
                                   (tag, name, filename,
                                    self.RenderXML(entry)))
                if fmt is not None and not fmt(entry.text):
                    self.LintError(
                        "required-attr-format",
                        "Text content of %s %s in %s is malformed\n%s" %
                        (tag, name, filename, self.RenderXML(entry)))

            if not attrs.issuperset(list(required_attrs.keys())):
                self.LintError(
                    "required-attrs-missing",
                    "The following required attribute(s) are missing for %s "
                    "%s in %s: %s\n%s" %
                    (tag, name, filename,
                     ", ".join([attr
                                for attr in
                                set(required_attrs.keys()).difference(attrs)]),
                     self.RenderXML(entry)))

            for attr, fmt in list(required_attrs.items()):
                if fmt and attr in attrs and not fmt(entry.attrib[attr]):
                    self.LintError(
                        "required-attr-format",
                        "The %s attribute of %s %s in %s is malformed\n%s" %
                        (attr, tag, name, filename, self.RenderXML(entry)))

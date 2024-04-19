""" Check files for various required comments. """

import os
import lxml.etree
import Bcfg2.Options
import Bcfg2.Server.Lint
from Bcfg2.Server import XI_NAMESPACE
from Bcfg2.Server.Plugins.Cfg.CfgPlaintextGenerator \
    import CfgPlaintextGenerator
from Bcfg2.Server.Plugins.Cfg.CfgGenshiGenerator import CfgGenshiGenerator
from Bcfg2.Server.Plugins.Cfg.CfgCheetahGenerator import CfgCheetahGenerator
from Bcfg2.Server.Plugins.Cfg.CfgJinja2Generator import CfgJinja2Generator
from Bcfg2.Server.Plugins.Cfg.CfgInfoXML import CfgInfoXML


class Comments(Bcfg2.Server.Lint.ServerPlugin):
    """ The Comments lint plugin checks files for header comments that
    give information about the files.  For instance, you can require
    SVN keywords in a comment, or require the name of the maintainer
    of a Genshi template, and so on. """

    options = Bcfg2.Server.Lint.ServerPlugin.options + [
        Bcfg2.Options.Option(
            cf=("Comments", "global_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for all file types"),
        Bcfg2.Options.Option(
            cf=("Comments", "global_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for all file types"),
        Bcfg2.Options.Option(
            cf=("Comments", "bundler_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for non-templated bundles"),
        Bcfg2.Options.Option(
            cf=("Comments", "bundler_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for non-templated bundles"),
        Bcfg2.Options.Option(
            cf=("Comments", "genshibundler_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for templated bundles"),
        Bcfg2.Options.Option(
            cf=("Comments", "genshibundler_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for templated bundles"),
        Bcfg2.Options.Option(
            cf=("Comments", "properties_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for Properties files"),
        Bcfg2.Options.Option(
            cf=("Comments", "properties_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for Properties files"),
        Bcfg2.Options.Option(
            cf=("Comments", "cfg_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for non-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "cfg_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for non-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "genshi_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for Genshi-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "genshi_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for Genshi-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "cheetah_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for Cheetah-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "cheetah_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for Cheetah-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "jinja2_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for Jinja2-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "jinja2_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for Jinja2-templated Cfg files"),
        Bcfg2.Options.Option(
            cf=("Comments", "infoxml_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for info.xml files"),
        Bcfg2.Options.Option(
            cf=("Comments", "infoxml_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for info.xml files"),
        Bcfg2.Options.Option(
            cf=("Comments", "probes_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for probes"),
        Bcfg2.Options.Option(
            cf=("Comments", "probes_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for probes"),
        Bcfg2.Options.Option(
            cf=("Comments", "metadata_keywords"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required keywords for metadata files"),
        Bcfg2.Options.Option(
            cf=("Comments", "metadata_comments"),
            type=Bcfg2.Options.Types.comma_list, default=[],
            help="Required comments for metadata files")]

    def __init__(self, *args, **kwargs):
        Bcfg2.Server.Lint.ServerPlugin.__init__(self, *args, **kwargs)
        self.config_cache = {}

    def Run(self):
        self.check_bundles()
        self.check_properties()
        self.check_metadata()
        self.check_cfg()
        self.check_probes()

    @classmethod
    def Errors(cls):
        return {"unexpanded-keywords": "warning",
                "keywords-not-found": "warning",
                "comments-not-found": "warning",
                "broken-xinclude-chain": "warning"}

    def required_keywords(self, rtype):
        """ Given a file type, fetch the list of required VCS keywords
        from the bcfg2-lint config.  Valid file types are documented
        in :manpage:`bcfg2-lint.conf(5)`.

        :param rtype: The file type
        :type rtype: string
        :returns: list - the required items
        """
        return self.required_items(rtype, "keyword")

    def required_comments(self, rtype):
        """ Given a file type, fetch the list of required comments
        from the bcfg2-lint config.  Valid file types are documented
        in :manpage:`bcfg2-lint.conf(5)`.

        :param rtype: The file type
        :type rtype: string
        :returns: list - the required items
        """
        return self.required_items(rtype, "comment")

    def required_items(self, rtype, itype):
        """ Given a file type and item type (``comment`` or
        ``keyword``), fetch the list of required items from the
        bcfg2-lint config.  Valid file types are documented in
        :manpage:`bcfg2-lint.conf(5)`.

        :param rtype: The file type
        :type rtype: string
        :param itype: The item type (``comment`` or ``keyword``)
        :type itype: string
        :returns: list - the required items
        """
        if itype not in self.config_cache:
            self.config_cache[itype] = {}

        if rtype not in self.config_cache[itype]:
            rv = []
            rv.extend(getattr(Bcfg2.Options.setup, "global_%ss" % itype))
            local_reqs = getattr(Bcfg2.Options.setup,
                                 "%s_%ss" % (rtype.lower(), itype))
            if local_reqs == ['']:
                # explicitly specified as empty
                rv = []
            else:
                rv.extend(local_reqs)
            self.config_cache[itype][rtype] = rv
        return self.config_cache[itype][rtype]

    def check_bundles(self):
        """ Check bundle files for required comments. """
        if 'Bundler' in self.core.plugins:
            for bundle in list(self.core.plugins['Bundler'].entries.values()):
                xdata = None
                rtype = ""
                try:
                    xdata = lxml.etree.XML(bundle.data)
                    rtype = "bundler"
                except (lxml.etree.XMLSyntaxError, AttributeError):
                    xdata = \
                        lxml.etree.parse(bundle.template.filepath).getroot()
                    rtype = "genshibundler"

                self.check_xml(bundle.name, xdata, rtype)

    def check_properties(self):
        """ Check Properties files for required comments. """
        if 'Properties' in self.core.plugins:
            props = self.core.plugins['Properties']
            for propfile, pdata in list(props.entries.items()):
                if os.path.splitext(propfile)[1] == ".xml":
                    self.check_xml(pdata.name, pdata.xdata, 'properties')

    def has_all_xincludes(self, mfile):
        """ Return True if :attr:`Bcfg2.Server.Lint.Plugin.files`
        includes all XIncludes listed in the specified metadata type,
        false otherwise. In other words, this returns True if
        bcfg2-lint is dealing with complete metadata.

        :param mfile: The metadata file ("clients.xml" or
                      "groups.xml") to check for XIncludes
        :type mfile: string
        :returns: bool
        """
        if self.files is None:
            return True
        else:
            path = os.path.join(self.metadata.data, mfile)
            if path in self.files:
                xdata = lxml.etree.parse(path)
                for el in xdata.findall('./%sinclude' % XI_NAMESPACE):
                    if not self.has_all_xincludes(el.get('href')):
                        self.LintError("broken-xinclude-chain",
                                       "Broken XInclude chain: could not "
                                       "include %s" % path)
                        return False

                return True

    def check_metadata(self):
        """ Check Metadata files for required comments. """
        if self.has_all_xincludes("groups.xml"):
            self.check_xml(os.path.join(self.metadata.data, "groups.xml"),
                           self.metadata.groups_xml.data,
                           "metadata")
        if hasattr(self.metadata, "clients_xml"):
            if self.has_all_xincludes("clients.xml"):
                self.check_xml(os.path.join(self.metadata.data, "clients.xml"),
                               self.metadata.clients_xml.data,
                               "metadata")

    def check_cfg(self):
        """ Check Cfg files and ``info.xml`` files for required
        comments. """
        if 'Cfg' in self.core.plugins:
            for entryset in list(self.core.plugins['Cfg'].entries.values()):
                for entry in list(entryset.entries.values()):
                    rtype = None
                    if isinstance(entry, CfgGenshiGenerator):
                        rtype = "genshi"
                    elif isinstance(entry, CfgPlaintextGenerator):
                        rtype = "cfg"
                    elif isinstance(entry, CfgCheetahGenerator):
                        rtype = "cheetah"
                    elif isinstance(entry, CfgJinja2Generator):
                        rtype = "jinja2"
                    elif isinstance(entry, CfgInfoXML):
                        self.check_xml(entry.infoxml.name,
                                       entry.infoxml.xdata,
                                       "infoxml")
                        continue
                    if rtype:
                        self.check_plaintext(entry.name, entry.data, rtype)

    def check_probes(self):
        """ Check Probes for required comments """
        if 'Probes' in self.core.plugins:
            for probe in list(self.core.plugins['Probes'].probes.entries.values()):
                self.check_plaintext(probe.name, probe.data, "probes")

    def check_xml(self, filename, xdata, rtype):
        """ Generic check to check an XML file for required comments.

        :param filename: The filename
        :type filename: string
        :param xdata: The file data
        :type xdata: lxml.etree._Element
        :param rtype: The type of file.  Available types are
                      documented in :manpage:`bcfg2-lint.conf(5)`.
        :type rtype: string
        """
        self.check_lines(filename,
                         [str(el)
                          for el in xdata.getiterator(lxml.etree.Comment)],
                         rtype)

    def check_plaintext(self, filename, data, rtype):
        """ Generic check to check a plain text file for required
        comments.

        :param filename: The filename
        :type filename: string
        :param data: The file data
        :type data: string
        :param rtype: The type of file.  Available types are
                      documented in :manpage:`bcfg2-lint.conf(5)`.
        :type rtype: string
        """
        self.check_lines(filename, data.splitlines(), rtype)

    def check_lines(self, filename, lines, rtype):
        """ Generic header check for a set of lines.

        :param filename: The filename
        :type filename: string
        :param lines: The data to check
        :type lines: list of strings
        :param rtype: The type of file.  Available types are
                      documented in :manpage:`bcfg2-lint.conf(5)`.
        :type rtype: string
        """
        if self.HandlesFile(filename):
            # found is trivalent:
            # False == keyword not found
            # None == keyword found but not expanded
            # True == keyword found and expanded
            found = dict((k, False) for k in self.required_keywords(rtype))

            for line in lines:
                # we check for both '$<keyword>:' and '$<keyword>$' to see
                # if the keyword just hasn't been expanded
                for (keyword, status) in list(found.items()):
                    if not status:
                        if '$%s:' % keyword in line:
                            found[keyword] = True
                        elif '$%s$' % keyword in line:
                            found[keyword] = None

            unexpanded = [keyword for (keyword, status) in list(found.items())
                          if status is None]
            if unexpanded:
                self.LintError("unexpanded-keywords",
                               "%s: Required keywords(s) found but not "
                               "expanded: %s" %
                               (filename, ", ".join(unexpanded)))
            missing = [keyword for (keyword, status) in list(found.items())
                       if status is False]
            if missing:
                self.LintError("keywords-not-found",
                               "%s: Required keywords(s) not found: $%s$" %
                               (filename, "$, $".join(missing)))

            # next, check for required comments.  found is just
            # boolean
            found = dict((k, False) for k in self.required_comments(rtype))

            for line in lines:
                for (comment, status) in list(found.items()):
                    if not status:
                        found[comment] = comment in line

            missing = [comment for (comment, status) in list(found.items())
                       if status is False]
            if missing:
                self.LintError("comments-not-found",
                               "%s: Required comments(s) not found: %s" %
                               (filename, ", ".join(missing)))

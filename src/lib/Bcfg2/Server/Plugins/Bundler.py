"""This provides bundle clauses with translation functionality."""

import copy
import lxml.etree
import os
import os.path
import re
import sys
import Bcfg2.Server
import Bcfg2.Server.Plugin
import Bcfg2.Server.Lint

try:
    import genshi.template.base
    import Bcfg2.Server.Plugins.TGenshi
    have_genshi = True
except:
    have_genshi = False


class BundleFile(Bcfg2.Server.Plugin.StructFile):
    def get_xml_value(self, metadata):
        bundlename = os.path.splitext(os.path.basename(self.name))[0]
        bundle = lxml.etree.Element('Bundle', name=bundlename)
        [bundle.append(copy.copy(item)) for item in self.Match(metadata)]
        return bundle


if have_genshi:
    class BundleTemplateFile(Bcfg2.Server.Plugins.TGenshi.TemplateFile,
                             Bcfg2.Server.Plugin.StructFile):
        def __init__(self, name, specific, encoding):
            Bcfg2.Server.Plugins.TGenshi.TemplateFile.__init__(self, name,
                                                               specific,
                                                               encoding)
            Bcfg2.Server.Plugin.StructFile.__init__(self, name)

        def get_xml_value(self, metadata):
            if not hasattr(self, 'template'):
                logger.error("No parsed template information for %s" %
                             self.name)
                raise Bcfg2.Server.Plugin.PluginExecutionError
            try:
                stream = self.template.generate(metadata=metadata).filter(
                    Bcfg2.Server.Plugins.TGenshi.removecomment)
                data = lxml.etree.XML(stream.render('xml',
                                                    strip_whitespace=False),
                                      parser=Bcfg2.Server.XMLParser)
                bundlename = os.path.splitext(os.path.basename(self.name))[0]
                bundle = lxml.etree.Element('Bundle', name=bundlename)
                for item in self.Match(metadata, data):
                    bundle.append(copy.deepcopy(item))
                return bundle
            except LookupError:
                lerror = sys.exc_info()[1]
                logger.error('Genshi lookup error: %s' % lerror)
            except genshi.template.TemplateError:
                terror = sys.exc_info()[1]
                logger.error('Genshi template error: %s' % terror)
                raise
            except genshi.input.ParseError:
                perror = sys.exc_info()[1]
                logger.error('Genshi parse error: %s' % perror)
            raise

        def Match(self, metadata, xdata):
            """Return matching fragments of parsed template."""
            rv = []
            for child in xdata.getchildren():
                rv.extend(self._match(child, metadata))
            logger.debug("File %s got %d match(es)" % (self.name, len(rv)))
            return rv


    class SGenshiTemplateFile(BundleTemplateFile):
        # provided for backwards compat
        pass


class Bundler(Bcfg2.Server.Plugin.Plugin,
              Bcfg2.Server.Plugin.Structure,
              Bcfg2.Server.Plugin.XMLDirectoryBacked):
    """The bundler creates dependent clauses based on the
       bundle/translation scheme from Bcfg1.
    """
    name = 'Bundler'
    __author__ = 'bcfg-dev@mcs.anl.gov'
    patterns = re.compile('^(?P<name>.*)\.(xml|genshi)$')

    def __init__(self, core, datastore):
        Bcfg2.Server.Plugin.Plugin.__init__(self, core, datastore)
        Bcfg2.Server.Plugin.Structure.__init__(self)
        self.encoding = core.encoding
        self.__child__ = self.template_dispatch
        try:
            Bcfg2.Server.Plugin.XMLDirectoryBacked.__init__(self,
                                                            self.data,
                                                            self.core.fam)
        except OSError:
            self.logger.error("Failed to load Bundle repository")
            raise Bcfg2.Server.Plugin.PluginInitError

    def template_dispatch(self, name, _):
        bundle = lxml.etree.parse(name,
                                  parser=Bcfg2.Server.XMLParser)
        nsmap = bundle.getroot().nsmap
        if (name.endswith('.genshi') or
            ('py' in nsmap and
             nsmap['py'] == 'http://genshi.edgewall.org/')):
            if have_genshi:
                spec = Bcfg2.Server.Plugin.Specificity()
                return BundleTemplateFile(name, spec, self.encoding)
            else:
                raise Bcfg2.Server.Plugin.PluginExecutionError("Genshi not available: %s" % name)
        else:
            return BundleFile(name, self.fam)

    def BuildStructures(self, metadata):
        """Build all structures for client (metadata)."""
        bundleset = []

        bundle_entries = {}
        for key, item in self.entries.items():
            bundle_entries.setdefault(self.patterns.match(os.path.basename(key)).group('name'),
                                      []).append(item)

        for bundlename in metadata.bundles:
            try:
                entries = bundle_entries[bundlename]
            except KeyError:
                self.logger.error("Bundler: Bundle %s does not exist" %
                                  bundlename)
                continue
            try:
                bundleset.append(entries[0].get_xml_value(metadata))
            except genshi.template.base.TemplateError:
                t = sys.exc_info()[1]
                self.logger.error("Bundler: Failed to template genshi bundle %s"
                                  % bundlename)
                self.logger.error(t)
            except:
                self.logger.error("Bundler: Unexpected bundler error for %s" %
                                  bundlename, exc_info=1)
        return bundleset


class BundlerLint(Bcfg2.Server.Lint.ServerPlugin):
    """ Perform various bundle checks """
    def Run(self):
        """ run plugin """
        self.missing_bundles()
        for bundle in self.core.plugins['Bundler'].entries.values():
            if (self.HandlesFile(bundle.name) and
                (not have_genshi or
                 not isinstance(bundle, BundleTemplateFile))):
                    self.bundle_names(bundle)

    @classmethod
    def Errors(cls):
        return {"bundle-not-found":"error",
                "inconsistent-bundle-name":"warning"}

    def missing_bundles(self):
        """ find bundles listed in Metadata but not implemented in Bundler """
        if self.files is None:
            # when given a list of files on stdin, this check is
            # useless, so skip it
            groupdata = self.metadata.groups_xml.xdata
            ref_bundles = set([b.get("name")
                               for b in groupdata.findall("//Bundle")])

            allbundles = self.core.plugins['Bundler'].entries.keys()
            for bundle in ref_bundles:
                xmlbundle = "%s.xml" % bundle
                genshibundle = "%s.genshi" % bundle
                if (xmlbundle not in allbundles and
                    genshibundle not in allbundles):
                    self.LintError("bundle-not-found",
                                   "Bundle %s referenced, but does not exist" %
                                   bundle)

    def bundle_names(self, bundle):
        """ verify bundle name attribute matches filename """
        try:
            xdata = lxml.etree.XML(bundle.data)
        except AttributeError:
            # genshi template
            xdata = lxml.etree.parse(bundle.template.filepath).getroot()

        fname = bundle.name.split('Bundler/')[1].split('.')[0]
        bname = xdata.get('name')
        if fname != bname:
            self.LintError("inconsistent-bundle-name",
                           "Inconsistent bundle name: filename is %s, "
                           "bundle name is %s" % (fname, bname))

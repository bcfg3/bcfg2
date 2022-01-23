""" PackagesSources handles the
:ref:`server-plugins-generators-packages` ``sources.xml`` file"""

import os
import sys
import Bcfg2.Server.Plugin
from Bcfg2.Server.Statistics import track_statistics
from Bcfg2.Server.Plugins.Packages.Source import SourceInitError


# pylint: disable=E0012,R0924
class PackagesSources(Bcfg2.Server.Plugin.StructFile):
    """ PackagesSources handles parsing of the
    :mod:`Bcfg2.Server.Plugins.Packages` ``sources.xml`` file, and the
    creation of the appropriate
    :class:`Bcfg2.Server.Plugins.Packages.Source.Source` object for
    each ``Source`` tag. """

    __identifier__ = None
    create = "Sources"

    def __init__(self, filename, cachepath, packages):
        """
        :param filename: The full path to ``sources.xml``
        :type filename: string
        :param cachepath: The full path to the directory where
                          :class:`Bcfg2.Server.Plugins.Packages.Source.Source`
                          data will be cached
        :type cachepath: string
        :param packages: The Packages plugin object ``sources.xml`` is
                         being parsed on behalf of (i.e., the calling
                         object)
        :type packages: Bcfg2.Server.Plugins.Packages.Packages

        :raises: :class:`Bcfg2.Server.Plugin.exceptions.PluginInitError` -
                 If ``sources.xml`` cannot be read
        """
        Bcfg2.Server.Plugin.StructFile.__init__(self, filename,
                                                should_monitor=True)

        #: The full path to the directory where
        #: :class:`Bcfg2.Server.Plugins.Packages.Source.Source` data
        #: will be cached
        self.cachepath = cachepath

        if not os.path.exists(self.cachepath):
            # create cache directory if needed
            try:
                os.makedirs(self.cachepath)
            except OSError:
                err = sys.exc_info()[1]
                self.logger.error("Could not create Packages cache at %s: %s" %
                                  (self.cachepath, err))

        #: The :class:`Bcfg2.Server.Plugins.Packages.Packages` that
        #: instantiated this ``PackagesSources`` object
        self.pkg_obj = packages

        #: The set of all XML files that have been successfully
        #: parsed.  This is used by :attr:`loaded` to determine if the
        #: sources have been fully parsed and the
        #: :class:`Bcfg2.Server.Plugins.Packages.Packages` plugin
        #: should be told to reload its data.
        self.parsed = set()

    def set_debug(self, debug):
        Bcfg2.Server.Plugin.StructFile.set_debug(self, debug)
        for source in self.entries:
            source.set_debug(debug)

    def HandleEvent(self, event=None):
        """ HandleEvent is called whenever the FAM registers an event.

        When :attr:`loaded` becomes True,
        :func:`Bcfg2.Server.Plugins.Packages.Packages.Reload` is
        called to reload all plugin data from the configured sources.

        :param event: The event object
        :type event: Bcfg2.Server.FileMonitor.Event
        :returns: None
        """
        if event and event.filename != self.name:
            for fpath in self.extras:
                if fpath == os.path.abspath(event.filename):
                    self.parsed.add(fpath)
                    break
        Bcfg2.Server.Plugin.StructFile.HandleEvent(self, event=event)
        if self.loaded:
            self.logger.info("Reloading Packages plugin")
            self.pkg_obj.Reload()

    @property
    def loaded(self):
        """ Whether or not all XML files (``sources.xml`` and
        everything XIncluded in it) have been parsed. This flag is
        used to determine if the Packages plugin should be told to
        load its data. """
        return sorted(list(self.parsed)) == sorted(self.extras)

    @track_statistics()
    def Index(self):
        Bcfg2.Server.Plugin.StructFile.Index(self)
        self.entries = []
        if self.loaded:
            for xsource in self.xdata.findall('.//Source'):
                source = self.source_from_xml(xsource)
                if source is not None:
                    self.entries.append(source)
            self.entries.sort(key=(lambda source: source.priority),
                              reverse=True)
    Index.__doc__ = Bcfg2.Server.Plugin.StructFile.Index.__doc__ + """

        ``Index`` is responsible for calling :func:`source_from_xml`
        for each ``Source`` tag in each file. """

    @track_statistics()
    def source_from_xml(self, xsource):
        """ Create a
        :class:`Bcfg2.Server.Plugins.Packages.Source.Source` subclass
        object from XML representation of a source in ``sources.xml``.
        ``source_from_xml`` determines the appropriate subclass of
        ``Source`` to instantiate according to the ``type`` attribute
        of the ``Source`` tag.

        :param xsource: The XML tag representing the source
        :type xsource: lxml.etree._Element
        :returns: :class:`Bcfg2.Server.Plugins.Packages.Source.Source`
                  subclass, or None on error
        """
        stype = xsource.get("type")
        if stype is None:
            self.logger.error("Packages: No type specified for source at %s, "
                              "skipping" % (xsource.get("rawurl",
                                                        xsource.get("url"))))
            return None

        cls = None
        for mod in Bcfg2.Options.setup.packages_backends:
            if mod.__name__.endswith(".%s" % stype.title()):
                cls = getattr(mod, "%sSource" % stype.title())
                break
        else:
            self.logger.error("Packages: Unknown source type %s" % stype)
            return None

        try:
            source = cls(self.cachepath, xsource)
        except SourceInitError:
            err = sys.exc_info()[1]
            self.logger.error("Packages: %s" % err)
            source = None

        return source

    def __getitem__(self, key):
        return self.entries[key]

    def __repr__(self):
        return "PackagesSources: %s" % repr(self.entries)

    def __str__(self):
        return "PackagesSources: %s sources" % len(self.entries)

    def __len__(self):
        return len(self.entries)

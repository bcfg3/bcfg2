""" Cfg creator that creates SSL certs """

import lxml.etree
from Bcfg2.Utils import Executor
from Bcfg2.Server.FileMonitor import get_fam
from Bcfg2.Server.Plugin import PluginExecutionError
from Bcfg2.Server.Plugins.Cfg import CfgCreationError, XMLCfgCreator, \
    CfgCreator


class CfgSSLCAFormatCreator(XMLCfgCreator):
    """ This class acts as both a Cfg creator that creates formatted
    SSL certs."""

    #: Different configurations for different clients/groups can be
    #: handled with Client and Group tags within pubkey.xml
    __specific__ = False

    #: Handle XML specifications of private keys
    __basenames__ = ['sslformat.xml']

    def __init__(self, fname):
        XMLCfgCreator.__init__(self, fname)
        self.cmd = Executor()

    def create_data(self, entry, metadata):
        """ generate a new formatted cert """
        self.logger.info("Cfg: Generating formatted SSL cert for %s" %
                         self.name)
        elem = self.XMLMatch(metadata).find("Format")
        certfile = None
        keyfile = None

        data = ''
        for part in elem:
            if part.tag == 'Key':
                if keyfile is None:
                    keyfile = self._get_keyfile(elem, metadata)
            
                cmd = ["openssl", "rsa", "-in", keyfile]
                if part.get('format') == 'der':
                    cmd.extend(['-outform', 'DER'])
                result = self.cmd.run(cmd)
                data += result.stdout
            elif part.tag == 'Cert':
                if certfile is None:
                    certfile = self._get_certfile(elem, metadata)
            
                cmd = ["openssl", "x509", "-in", certfile]
                if part.get('format') == 'der':
                    cmd.exend(['-outform', 'DER'])
                result = self.cmd.run(cmd)
                data += result.stdout
            else:
                raise CfgCreationError("Cfg: Unknown SSL Cert format "
                                       "%s for %s" % (part.tag, self.name))
        self.write_data(data, **self.get_specificity(metadata))
        return data

    def _get_keyfile(self, elem, metadata):
        """ Given a <Format/> element and client metadata, return the
        full path to the file on the filesystem that the key lives in."""
        keypath = elem.get("key", None)
        if keypath is not None:
            eset = self.cfg.entries[keypath]
            try:
                return eset.best_matching(metadata).name
            except PluginExecutionError:
                raise CfgCreationError("Cfg: No SSL Key found at %s" %
                                       keypath)
        else:
            # Get ssl key from cert creator
            certpath = elem.get("cert")
            eset = self.cfg.entries[certpath]
            try:
                creator = eset.best_matching(metadata,
                                             eset.get_handlers(metadata,
                                                               CfgCreator))
            except PluginExecutionError:
                raise CfgCreationError("Cfg: No SSL cert creator defined "
                                       "for %s" % certpath)

            cert = creator.XMLMatch(metadata).find("Cert")
            return creator._get_keyfile(cert, metadata)

    def _get_certfile(self, elem, metadata):
        """ Given a <Format/> element and client metadata, return the
        full path to the file on the filesystem that the cert lives in."""
        certpath = elem.get("cert")
        eset = self.cfg.entries[certpath]
        try:
            return eset.best_matching(metadata).name
        except PluginExecutionError:
            # SSL cert needs to be created
            try:
                creator = eset.best_matching(metadata,
                                             eset.get_handlers(metadata,
                                                               CfgCreator))
            except PluginExecutionError:
                raise CfgCreationError("Cfg: No SSL Cert or cert creator "
                                       "defined for %s" % certpath)

            certentry = lxml.etree.Element("Path", name=certpath)
            creator.create_data(certentry, metadata)

            tries = 0
            while True:
                if tries >= 10:
                    raise CfgCreationError("Cfg: Timed out waiting for event "
                                           "on SSL cert at %s" % certpath)
                get_fam().handle_events_in_interval(1)
                try:
                    return eset.best_matching(metadata).name
                except PluginExecutionError:
                    tries += 1
                    continue

""" ``bcfg2-lint`` plugin for :ref:`TemplateHelper
<server-plugins-connectors-templatehelper>` """

import sys
import imp
from Bcfg2.Server.Lint import ServerPlugin
from Bcfg2.Server.Plugins.TemplateHelper import HelperModule, MODULE_RE
from Bcfg2.Utils import safe_module_name


class TemplateHelper(ServerPlugin):
    """ ``bcfg2-lint`` plugin to ensure that all :ref:`TemplateHelper
    <server-plugins-connectors-templatehelper>` modules are valid.
    This can check for:

    * A TemplateHelper module that cannot be imported due to syntax or
      other compile-time errors;
    * A TemplateHelper module that does not have an ``__export__``
      attribute, or whose ``__export__`` is not a list;
    * Bogus symbols listed in ``__export__``, including symbols that
      don't exist, that are reserved, or that start with underscores.
    """
    __serverplugin__ = 'TemplateHelper'

    def __init__(self, *args, **kwargs):
        ServerPlugin.__init__(self, *args, **kwargs)
        # we instantiate a dummy helper to discover which keywords and
        # defaults are reserved
        dummy = HelperModule("foo.py", None)
        self.reserved_keywords = dir(dummy)
        self.reserved_defaults = dummy.reserved_defaults

    def Run(self):
        for helper in list(self.core.plugins['TemplateHelper'].entries.values()):
            if self.HandlesFile(helper.name):
                self.check_helper(helper.name)

    def check_helper(self, helper):
        """ Check a single helper module.

        :param helper: The filename of the helper module
        :type helper: string
        """
        module_name = MODULE_RE.search(helper).group(1)

        try:
            module = imp.load_source(
                safe_module_name('TemplateHelper', module_name), helper)
        except:  # pylint: disable=W0702
            err = sys.exc_info()[1]
            self.LintError("templatehelper-import-error",
                           "Failed to import %s: %s" %
                           (helper, err))
            return

        if not hasattr(module, "__export__"):
            self.LintError("templatehelper-no-export",
                           "%s has no __export__ list" % helper)
            return
        elif not isinstance(module.__export__, list):
            self.LintError("templatehelper-nonlist-export",
                           "__export__ is not a list in %s" % helper)
            return

        for sym in module.__export__:
            if not hasattr(module, sym):
                self.LintError("templatehelper-nonexistent-export",
                               "%s: exported symbol %s does not exist" %
                               (helper, sym))
            elif sym in self.reserved_keywords:
                self.LintError("templatehelper-reserved-export",
                               "%s: exported symbol %s is reserved" %
                               (helper, sym))
            elif sym.startswith("_"):
                self.LintError("templatehelper-underscore-export",
                               "%s: exported symbol %s starts with underscore"
                               % (helper, sym))
            if sym in getattr(module, "__default__", []):
                self.LintError("templatehelper-export-and-default",
                               "%s: %s is listed in both __default__ and "
                               "__export__" % (helper, sym))

        for sym in getattr(module, "__default__", []):
            if sym in self.reserved_defaults:
                self.LintError("templatehelper-reserved-default",
                               "%s: default symbol %s is reserved" %
                               (helper, sym))

    @classmethod
    def Errors(cls):
        return {"templatehelper-import-error": "error",
                "templatehelper-no-export": "error",
                "templatehelper-nonlist-export": "error",
                "templatehelper-nonexistent-export": "error",
                "templatehelper-reserved-export": "error",
                "templatehelper-reserved-default": "error",
                "templatehelper-underscore-export": "warning",
                "templatehelper-export-and-default": "warning"}

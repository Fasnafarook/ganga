##########################################################################
# Ganga Project. https://github.com/ganga-devs/ganga
#
# $Id: gangadoc.py,v 1.1 2008-07-17 16:41:00 moscicki Exp $
##########################################################################

"""Improved support for interactive help based on pydoc.
Remove hardcoded limits on the help text.
This module makes changes to the content of the pydoc module.
"""


import pydoc

_GPIhelp = '''Ganga Public Interface (GPI) Index

%(Classes)s

%(Exceptions)s

%(Functions)s

%(Objects)s

'''

from GangaCore.Utility.logging import getLogger
logger = getLogger(modulename=True)

_GPIhelp_sections = {
    'Classes': [], 'Exceptions': [], 'Functions': [], 'Objects': []}


def adddoc(name, object, doc_section, docstring):
    '''
    Add automatic documentation to gangadoc system.
    "doc_section" specifies how the object should be documented.
    If docstring is specified then use it to document the object. Otherwise use __doc__ (via pydoc utilities).
    '''
    from GangaCore.Utility.logic import implies
    assert (implies(docstring, doc_section == "Objects"))
    # assert(not docstring and not object.__doc__)

    _GPIhelp_sections[doc_section] += [(name, object, docstring)]


def makedocindex():
    '''
    Return a string with GPI Index.
    '''

    import pydoc

    sections = {}

    from GangaCore.Utility.strings import ItemizedTextParagraph

    for sec, names in zip(list(_GPIhelp_sections.keys()), list(_GPIhelp_sections.values())):
        itbuf = ItemizedTextParagraph(sec + ':')
        for name, obj, docstring in names:
            # if docstring not provided when exporting the object to GPI then
            # use the docstring generated by pydoc
            if not docstring:
                docstring = pydoc.splitdoc(pydoc.getdoc(obj))[0]
            itbuf.addLine(name, docstring)

        sections[sec] = itbuf.getString()

    return _GPIhelp % sections


# modifications to pydoc module

# a workaround for hardcoded limit of maxlen==70 characters
class TextDoc2(pydoc.TextDoc):

    def docother(self, object, name=None, mod=None, maxlen=None, doc=None):
        return pydoc.TextDoc.docother(self, object, name=name, mod=mod, doc=doc)


class Helper2(pydoc.Helper):

    def __init__(self, *args, **kwds):
        pydoc.Helper.__init__(self, *args, **kwds)

    def intro(self):

        from GangaCore.Runtime import _prog

        self.output.write("""************************************
%s

This is an interactive help based on standard pydoc help.

Type 'index'  to see GPI help index.
Type 'python' to see standard python help screen.
Type 'interactive' to get online interactive help from an expert.
Type 'quit'   to return to GangaCore.
************************************
""" % (_prog.hello_string))

    def help(self, request):
        if isinstance(request, str):
            if request == 'python':
                pydoc.Helper.intro(self)
                return

            if request == 'index':
                self.output.write(makedocindex())
                return

            if request == 'interactive':
                from . import eliza
                self.output.write("""
This is an interactive help. At the prompt type your questions in plain english\n\n""")
                eliza.command_interface()
                return

            # eval the expression (in the context of GangaCore.GPI namespace)
            from .gangadoceval import evaluate
            request = evaluate(request)

        return pydoc.Helper.help(self, request)


pydoc.text = TextDoc2()
pydoc.text._repr_instance.maxstring = 255
pydoc.text._repr_instance.maxother = 70

import sys

pydoc.help = Helper2(sys.stdin, sys.stdout)


# bugfix: #18012 overview: No help text avaialable for "jobs"
# with python2.4 should not be needed (?)
# patch the  doc method  from pydoc module  to support  documenting, in
# case of  af an instance,  the structure of  its class instead  of its
# value
# &
# bugfix: #12584
# overview: for some (unknown) reason the IPython code inserts an instance of
# IPython.FakeModule.FakeModule class in sys.modules
# inspect.getmodule(object) method raises in this a TypeError
# workaround: use an improved getmodule(object) method that does supplementary checks
# Notes:
# Running with Python2.2 IPython seems to insert a *stripped* version of FakeModule in sys.module which masks this bug
# This bug persists in IPython/Python 2.4 too


modulesbyfile = {}
import inspect


def mygetmodule(object):
    """Return the module an object was defined in, or None if not found."""
    import os.path
    if inspect.ismodule(object):
        return object
    if hasattr(object, '__module__'):
        return sys.modules.get(object.__module__)
    try:
        file = inspect.getabsfile(object)
    except TypeError:
        return None
    if file in modulesbyfile:
        return sys.modules.get(modulesbyfile[file])
    for module in sys.modules.values():
        # check if value is indeed a module
        if inspect.ismodule(module) and hasattr(module, '__file__'):
            modulesbyfile[
                os.path.realpath(inspect.getabsfile(module))] = module.__name__
    if file in modulesbyfile:
        return sys.modules.get(modulesbyfile[file])
    main = sys.modules['__main__']
    if not hasattr(object, '__name__'):
        return None
    if hasattr(main, object.__name__):
        mainobject = getattr(main, object.__name__)
        if mainobject is object:
            return main
    builtin = sys.modules['__builtin__']
    if hasattr(builtin, object.__name__):
        builtinobject = getattr(builtin, object.__name__)
        if builtinobject is object:
            return builtin


def doc2(thing, title='Python Library Documentation: %s', forceload=0, output=None):
    """Display text documentation, given an object or a path to an object."""
    try:
        object, name = pydoc.resolve(thing, forceload)
        desc = pydoc.describe(object)
        module = mygetmodule(object)
        if name and '.' in name:
            desc += ' in ' + name[:name.rfind('.')]
        elif module and module is not object:
            desc += ' in module ' + module.__name__

        if not (inspect.ismodule(object)
                or inspect.isclass(object)
                or inspect.isroutine(object)
                or isinstance(object, property)):
            # If the passed object is a piece of data or an instance,
            # document its available methods instead of its value.

            object = type(object)
            desc += ' object'
        pydoc.pager(title % desc + '\n\n' + pydoc.text.document(object, name))
    except (ImportError, pydoc.ErrorDuringImport) as value:
        logger.error(value)


pydoc.doc = doc2


#
#
# $Log: not supported by cvs2svn $
# Revision 1.6  2007/07/10 13:08:32  moscicki
# docstring updates (ganga devdays)
#
# Revision 1.5  2006/08/09 08:55:13  adim
# bugfix: #12584
# overview: IPython code inserts an instance of IPython.FakeModule.FakeModule class in sys.modules
# which breaks the help system.
#
# Revision 1.4  2006/07/12 12:40:45  moscicki
# bugfix: #18012 overview: No help text avaialable for "jobs"
#
# Revision 1.3  2006/02/10 14:17:08  moscicki
# fixed bugs:
# #14136 help system doesn't find documentation.
#
# Revision 1.2  2005/08/31 15:06:14  andrew
# add the interactive help system
#
# Revision 1.1  2005/08/24 15:24:11  moscicki
# added docstrings for GPI objects and an interactive ganga help system based on pydoc
#
#
#

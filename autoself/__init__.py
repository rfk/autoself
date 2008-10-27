"""

    autoself:  automagically add method definition boilerplate

First, a disclaimer.  Explicit self is good.  Bytecode hacks are bad.
Put them together and it's quite clear that THIS MODULE IS AN ABOMINATION!
But, it's a neat excursion into python's lower levels and if you *really*
*really* want to save yourself some keystrokes (like, you're desperately
trying to hack into the Death Star's security system to override the trash
compactor as its cold metal jaws slowly squeeze you to a purple paste) then
it can help you do that.  But, stop and consider Guido's proclamation on
the matter:

  Having self be explicit is a *good thing*. It makes the code clear by
  removing ambiguity about how a variable resolves. It also makes the
  difference between functions and methods small.
     "Things that will Not Change in Python 3000":
     http://www.python.org/dev/peps/pep-3099/#core-language

This module is not about making 'self' implicit.  It doesn't try to change
the way methods work, or make any semantic changes whatsoever.  It does one
simple thing: automatically adds the boilerplate code to make a function do
the "right thing" when called as a method.

It provides a single function 'autoself'.  Given a function as argument,
'autoself' will return an equivalent function with the necessary boilerplate
in place to act as a method.  This will depend on the specifics of the
function, and could mean:

  * Inserting 'self' as the zeroth argument
  * Inserting 'cls' as the zeroth argument, and wrapping with classmethod()
  * Wrapping with staticmethod() if 'self' and 'cls' are not used
  * Doing nothing, if it's not a proper function or is fine the way it is

For example, defining the method 'likes' using:

    def likes(self,ham,eggs):
        print self, "likes", ham, "and", eggs

Is equivalent to defining it in the following way:

    def likes(ham,eggs):
        print self, "likes", ham, "and", eggs
    likes = autoself(likes)

Or neater, using the @autoself decorator.  Of course, this isn't going to
save you any typing!  'autoself' can also be applied to a class, and will
autoselfify all functions in that class's dict:

   class HeapsLessTyping:
      def likes(ham,eggs):
        # This gets 'self' automatically added as zeroth argument
        print self, "likes", ham, "and", eggs
      def hates(spam):
        # This becomes a classmethod, with 'cls' added as zeroth argument
        print "all", cls, "hate", spam
      def meh(toast):
        # This becomes a staticmethod
        print toast, "is boring"
   HeapsLessTyping = autoself(HeapsLessTyping)

When it becomes available (Python 2.6?), it will be even more convenient to
use this with the class decorator syntax.

Want to save even more typing?  'autoself' can be used as a metaclass to
work its magic on all classes defined in a module:

   __metaclass__ = autoself

   class LookNoSelf:
       def __init__(my,special,args):
           self.my = my
           self.special = special
           self.args = args
   class FiveKeystrokesSaved:
       def __init__(this,works,great):
           self.this = this
           self.works = works
           self.great = great
       counter = 0
       def ClassMethodsSaveEvenMore():
           cls.counter += 1

Using this style, you can see a net saving in keystrokes with five method
definitions or less!
"""

__ver_major__ = 1
__ver_minor__ = 1
__ver_patch__ = 0
__ver_sub__ = ""
__version__ = "%d.%d.%d%s" % (__ver_major__,__ver_minor__,
                              __ver_patch__,__ver_sub__)

import types
import dis
import os
import sys
import unittest


class _NoSuchVar(Exception):
    """Raised when a requested variable is not used in a function."""
    pass

def autoself(obj,cbases=None,cdict=None):
    """Automatic boilerplate to make functions into methods.

    This function modifies other functions to make them do the
    "right thing" when called as methods. It can be called with the
    following types of argument:

        * a function:  returns a new function with boilerplate in place
        * a class:     autoselfifies all applicable methods in class dict
        * other:       returns the object unmodified

    Functions are transformed according to the following rules:

      1) if 'self' is used as a non-local, promote it to the zeroth argument
      2) if 'cls' is used as a non-local, and 'self' is not the zeroth
         argument, add 'cls' in that position and wrap in classmethod()
      3) if neither 'self' nor 'class' are the zeroth argument, wrap
         with staticmethod()

    This function can also be used as a metaclass, if provided with
    the appropriate three arguments instead of the usual one.
    """
    # Three arguments given, we're creating a class
    if cbases is not None and cdict is not None:
        klass = type(obj,cbases,cdict)
        return autoself(klass)
    # A proper function - create autoselfified version
    if type(obj) == types.FunctionType:
        try:
            return _makeArg0(obj,"self")
        except _NoSuchVar:
            try:
                return classmethod(_makeArg0(obj,"cls"))
            except _NoSuchVar:
                return staticmethod(obj)
    # A class - autoselfify all entries in __dict__
    if type(obj) in (type,types.ClassType):
        for mn in obj.__dict__:
            m = obj.__dict__[mn]
            am = autoself(m)
            # Must use setattr on new-style classes, __dict__ is not writable.
            if m is not am:
              setattr(obj,mn,am)
        return obj
    # Something else - do not modify
    return obj

def _makeArg0(f,nm):
    """Promote the named variable from non-local to argument zero.
    If the zeroth argument already has that name, return the function
    unmodified.  If the function does not refer to that variable name,
    raise _NoSuchVar exception.
    """
    fc = f.func_code
    # Check whether it is already in position
    try:
      if fc.co_varnames[0] == nm:
        return f
    except IndexError:
        pass
    # Locate the variable in names and freevars list.
    # If it's not in either, the function doesn't refer to that variable
    try:
       idxNM = list(fc.co_names).index(nm)
    except ValueError:
        idxNM = -1
    try:
        idxFV = len(fc.co_cellvars) + list(fc.co_freevars).index(nm)
    except ValueError:
        idxFV = -1
    if idxNM == -1 and idxFV == -1:
        raise _NoSuchVar()
    # Add it as the first argument, and fix up the bytecode
    newVars = tuple([nm] + list(fc.co_varnames))
    newCode = "".join(_fixArg0(fc.co_code,idxNM,idxFV))
    # Create new code and function objects, and return
    c = types.CodeType(fc.co_argcount+1,fc.co_nlocals+1,fc.co_stacksize+1,
                       fc.co_flags,newCode,fc.co_consts,fc.co_names,newVars,
                       fc.co_filename,fc.co_name,fc.co_firstlineno,
                       fc.co_lnotab,fc.co_freevars,fc.co_cellvars)
    withArg0 = types.FunctionType(c,f.func_globals,f.func_name,
                                    f.func_defaults,f.func_closure)
    return withArg0

# Opcodes that operate on names/vars, and the corresponding opcode for local
# vars. These need to be translated in the bytecode.
_name2local = { 'STORE_NAME': 'STORE_FAST',
                'DELETE_NAME': 'DELETE_FAST',
                'STORE_GLOBAL': 'STORE_FAST',
                'DELETE_GLOBAL': 'DELETE_FAST',
                'LOAD_NAME': 'LOAD_FAST',
                'LOAD_GLOBAL': 'LOAD_FAST',
                'LOAD_DEREF': 'LOAD_FAST',
                'STORE_DEREF': 'STORE_FAST'}

def _fixArg0(code,nmIdx,fvIdx):
    """Fix bytecode to treat a var as an argument rather than a name.
    'code' is the bytecode to be modified, 'nmIdx' and 'fvIdx' are the
    position of the target var in the names and freevars arrays respectively.
    The following transforms are applied:
        * opcodes taking a local as argument have their argument incremented
          by one, to account for the new arg at position zero
        * opcodes treating the var as a name are modified to use local var zero
        * opcodes derefrencing cellvar fvIdx are modified to use local var zero
    """
    ops = iter(code)
    for op in ops:
      op = ord(op)
      if op < dis.HAVE_ARGUMENT:
        yield chr(op)
      else:
        arg = ord(ops.next()) + ord(ops.next())*256
        if op in dis.haslocal:
          arg = arg + 1
        elif op in dis.hasname and arg == nmIdx:
          opname = dis.opname[op]
          if opname in _name2local:
            opname = _name2local[opname]
            op = dis.opmap[opname]
            arg = 0
        elif op in dis.hasfree and arg == fvIdx:
          opname = dis.opname[op]
          if opname in _name2local:
            opname = _name2local[opname]
            op = dis.opmap[opname]
            arg = 0
        yield chr(op)
        yield chr(arg % 256)
        yield chr(arg // 256)
            

##  Testsuite begins here

def _test0():
    """A very simple function for testing purposes."""
    return self
class _testC:
    """A very simple class for testing purposes."""
    def __init__(input):
        self.input = input
    def meth1(*args):
        return (self,args)
    def cmeth(*args):
        return (cls,args)
    def smeth(*args):
        return args

class TestSimple(unittest.TestCase):
 
    def test_ZeroArg(self):
        """Test whether 'self' is actually inserted"""
        asf = autoself(_test0)
        self.assertEqual(42,asf(42))

    def test_DoubleApp(self):
        """Test whether double application leaves it alone."""
        asf = autoself(_test0)
        asf2 = autoself(asf)
        self.assert_(asf is not _test0)
        self.assert_(asf is asf2)
        
    def test_PosArgs(self):
        """Test whether positional arguments are maintained correctly."""
        def tester(a1,a2):
          if self == self: pass
          return (a1,a2)
        tester = autoself(tester)
        res = tester(None,42,"bacon")
        self.assertEqual(res,(42,"bacon"))

    def test_StarArg(self):
        """Test whether *arg works correctly."""
        def tester(a1,*arg):
            return (self,a1,arg)
        tester = autoself(tester)
        res = tester("spam",13,"more","args")
        self.assertEqual(res,("spam",13,("more","args")))

    def test_StarKwd(self):
        """Test whether **kwd works correctly."""
        def tester(a1,*arg,**kwd):
            return (self,a1,arg,kwd)
        tester = autoself(tester)
        res = tester("self",13,"pos","args",key1="val1",key2="val2")
        self.assertEqual(res,("self",13,("pos","args"),{"key1":"val1","key2":"val2"}))


class TestClass(unittest.TestCase):

    def test_BasicClass(self):
        """Test whether classes are transformed correctly."""
        asc = autoself(_testC)
        i = _testC(42)
        self.assertEqual(i.input,42)
        self.assertEqual(i.meth1("ham","eggs"),(i,("ham","eggs")))
        self.assertEqual(i.cmeth("ham","eggs"),(asc,("ham","eggs")))
        self.assertEqual(i.smeth("ham","eggs"),("ham","eggs"))
        self.assertEqual(type(asc.__dict__['meth1']),types.FunctionType)
        self.assertEqual(type(asc.__dict__['cmeth']),classmethod)
        self.assertEqual(type(asc.__dict__['smeth']),staticmethod)

    def test_ClassMethod(self):
        """Test whether class methods act as we expect"""
        class tester:
          counter = 0
          def inc(n):
            cls.counter += n
          def get():
            return cls.counter
        tester = autoself(tester)
        t1 = tester()
        t2 = tester()
        self.assertEqual(t1.counter,0)
        self.assertEqual(tester.counter,0)
        t2.inc(1)
        self.assertEqual(t1.counter,1)
        self.assertEqual(tester.counter,1)
        self.assertEqual(t2.get(),1)
        t1.inc(2)
        self.assertEqual(tester.counter,3)
        tester.inc(3)
        self.assertEqual(t2.get(),6)
      
    def test_ExClassMethod(self):
        """Test whether existing class methods are left alone."""
        class tester(object):
            def meth1(arg):
                return (self,arg)
            def cmeth(cls,*args):
                return (cls,args)
            cmeth = classmethod(cmeth)
        tester = autoself(tester)
        i = tester()
        self.assertEqual(i.meth1(42),(i,42))
        self.assertEqual(i.cmeth(1,2),(tester,(1,2)))

class TestMetaClass(unittest.TestCase):

    def test_BasicMeta(self):
        """Test whether metaclass definition works."""
        class tester(object):
            __metaclass__ = autoself
            def __init__(color):
              self.color = color
        i = tester("blue")
        self.assertEqual(i.color,"blue")

    def test_ModMeta(self):
        """Test whether module-level metaclass works."""
        import autoself.testmeta


def testsuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSimple))
    suite.addTest(unittest.makeSuite(TestClass))
    suite.addTest(unittest.makeSuite(TestMetaClass))
    return suite

def runtestsuite():
    unittest.TextTestRunner().run(testsuite())

if __name__ == "__main__":
    runtestsuite()



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

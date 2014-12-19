# iosapplist
# A Python package that lists iOS App Store apps.  (Formerly part of AppBackup.)
#
# Copyright (C) 2008-2014 Scott Zeid
# https://s.zeid.me/projects/appbackup/
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# 
# Except as contained in this notice, the name(s) of the above copyright holders
# shall not be used in advertising or otherwise to promote the sale, use or
# other dealings in this Software without prior written authorization.

# Output stuff

from __future__ import with_statement

from command import Command


__all__ = ["error", "normal"]


class OutputCommand(Command):
 """Used internally by some commands."""
 
 name = ["<fill-this-in>"]
 sort_group = float("-inf")
 add_args = False
 
 def main(self, cli):
  if len(self.argv) != 4:
   yield stop(127)
  argv0, stop_value, normal_value, error_value = self.argv
  try:
   stop_value = int(stop_value)
  except ValueError:
   yield stop(127)
  if not isinstance(normal_value, (list, tuple)):
   normal_value = (normal_value,)
  if not isinstance(error_value, (list, tuple)):
   error_value = (error_value,)
  for value in error_value:
   yield error(value)
  for value in normal_value:
   yield normal(value)
  yield stop(stop_value)


def error(value, human=None):
 return item("error", value, human)


def normal(value, human=None):
 return item("normal", value, human)


def stop(value, human=None):
 return item("stop", value, human)


def item(type, value, human=None):
 return _OutputItem(type, value, human)


class _OutputItem(object):
 __doc__ = None
 def __new__(cls, type, value, human):
  # hack hack hackity hack
  class item(cls):
   __doc__ = cls.__doc__
   def __new__(item_cls):
    return object.__new__(item_cls)
   @property
   def type(self):
    return type
   @property
   def value(self):
    return value
   @property
   def human(self):
    return human
   def __repr__(self):
    return "<%s (%s): %s>" % (cls.__name__, self.type, repr(self.value))
   def __str__(self):
    return repr(self)
   def __unicode__(self):
    return repr(self).decode("utf-8")
  r = item()
  r.__name__ = cls.__name__
  return r

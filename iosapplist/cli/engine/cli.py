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

# Base CLI engine

import types

import commands

from command import Command
from commandlist import CommandList


__all__ = ["CLI", "CLIError"]


class CLIError(Exception):
 pass


def make_CLI_class():
 class base:
  cls = None
 base = base()
 
 class CLI(object):
  class __meta(type):
   def __new__(mcs, name, bases, dict):
    cls = type.__new__(mcs, name, bases, dict)
    if base.cls is None:
     base.cls = cls
     cls.commands = None
    if cls.commands is not None:
     for supercls in cls.__mro__[1:]:
      if issubclass(supercls, base.cls):
       cls.commands = supercls.commands.copy()
       break
    if cls.commands is None:
     cls.commands = CommandList()
     cls.commands.register(commands)
    return cls
  __metaclass__ = __meta
  
  __output_format = None
  
  default_command = basestring
  description = None
  program = None
  
  def __call__(self, argv, default=None.__class__):
   argv0 = argv[0] if len(argv) else None
   cmd = self.commands.get(argv0, None)
   default = self.default_command if default is None.__class__ else default
   if not cmd:
    cmd = self.commands.get(default, None)
    if cmd:
     argv = [default] + argv
    else:
     if argv0:
      raise CLIError("%s is not a valid command" % argv0)
     else:
      raise CLIError("no command given")
   return cmd(self).run(argv)
 
 return CLI

CLI = make_CLI_class()

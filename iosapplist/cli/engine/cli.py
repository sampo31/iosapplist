# iosapplist
# A Python package that lists iOS App Store apps.  (Formerly part of AppBackup.)
#
# Copyright (C) 2008-2015 Scott Zeid
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

import sys
import types

import commands

from . import debug
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
     debug("copying command registry from superclass")
     for supercls in cls.__mro__[1:]:
      if issubclass(supercls, base.cls):
       cls.commands = supercls.commands.copy()
       break
    if cls.commands is None:
     debug("making new command registry")
     cls.commands = CommandList()
     cls.commands.register(commands)
    debug("done assigning command registry")
    return cls
  __metaclass__ = __meta
  
  __output_format = None
  __started_any = False
  
  default_command = None
  description = None
  easter_eggs = False
  program = None
  version = None
  
  def start(self, argv, parent_cmd=None, default=None.__class__,
            verbose_return=False):
   argv = (["shell"] if not self.__started_any else []) + argv
   debug("running", argv, "in a new instance")
   cmd, argv = self._lookup(argv, parent_cmd, default)
   if not self.__started_any:
    cmd._ShellCommand__is_shell = False
   self.__started_any = True
   r = cmd.run(argv)
   debug("finished running", argv)
   if verbose_return:
    return r, cmd
   return r
  
  def __call__(self, argv, parent_cmd=None, default=None.__class__):
   cmd, argv = self._lookup(argv, parent_cmd, default)
   debug("running", argv)
   generator = cmd.generate_output(argv)
   while True:
    try:
     item = generator.next()
     yield item
    except StopIteration, exc:
     debug("finished running", argv)
     while True:
      raise exc
  
  def _lookup(self, argv, parent_cmd=None, default=None.__class__):
   debug("preparing to run", argv)
   argv0 = argv[0] if len(argv) else None
   cmd = self.commands.get(argv0, None)
   default_arg = default
   default = self.default_command if default is None.__class__ else default
   doing_help = False
   if not cmd:
    debug("getting object for default command:", default)
    cmd = self.commands.get(default, None)
    if cmd:
     argv = [default] + argv
    else:
     if argv0 or (not argv0 and default_arg is not None.__class__):
      raise CLIError("%s is not a valid command" % argv0)
     else:
      doing_help = True
      cmd = self.commands["shell"]
      argv = ["sh", "--help"]
   cmd = cmd(self)
   if parent_cmd:
    cmd.stdin = parent_cmd.stdin
    cmd.stdout = parent_cmd.stdout
    cmd.stderr = parent_cmd.stderr
   if doing_help:
    cmd._ShellCommand__is_shell = False
   return cmd, argv
 
 return CLI

CLI = make_CLI_class()

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

# shell command

from __future__ import with_statement

import argparse
import array
import plistlib
import re
import readline
import shlex
import sys

try:
 import json
except ImportError:
 import simplejson as json
import traceback

from .. import Command, output, debug
from ..cli import CLIError


__all__ = ["ShellCommand"]


class ShellCommand(Command):
 """Starts an interactive shell."""
 
 names = ["shell", "sh"]
 add_help = False
 description = None
 easter_eggs = False
 #names = ["command", "cmd"]
 sort_group = -3
 usage = "[options [...]] [command [args [...]]]"
 
 __is_shell = False
 
 __robot_easter_egg_triggers = ("true", "yes", "on", "y", "1")
 __use_real_output_format = True
 
 @property
 def output_format(self):
  return self.real_output_format if self.__use_real_output_format else ""
 
 def add_args(self, p, cli):
  p.usage = self.usage
  p.description = self.description or cli.description
  p.add_argument("--help", "-h", action="store_true",
                 help='Shows help about the program or a command.')
  if self.easter_eggs:
   p.add_argument("--hep", action="store_true", help=argparse.SUPPRESS)
  p.add_argument("--robot", default="", metavar='<format>',
                 help='Produce output suitable for robots.'
                      '  Format should be "plist" or "json".')
  if self.__is_shell:
   p.add_argument("--ps1", default="> ",
                  help='The string to use to prompt for shell input ("> " by'
                       ' default).  -0 supersedes this option.')
   p.add_argument("-0", "--null", action="store_true",
                  help='Prompt for and terminate shell input with a null byte'
                       ' instead of, respectively, ps1 and a newline.  Useful'
                       ' in conjunction with --robot.')
  p.formatter_class = argparse.RawDescriptionHelpFormatter
  if not self.__is_shell:
   p.epilog = "commands"
   if cli.default_command:
    p.epilog += " (default is `%s`)" % cli.default_command
   p.epilog += ":"
   sort_group = n = 0
   for cmd in cli.commands:
    if cmd.show_in_help:
     names = cmd.names if not cmd.names_are_aliases else (cmd.names,)
     for name in names:
      name = name if isinstance(name, (list, tuple)) else (name,)
      if n and cmd.sort_group < 0 and sort_group >= 0:
       p.epilog += "\n"
      if n and cmd.sort_group == float("-inf") and sort_group != float("-inf"):
       p.epilog += "\n"
      sort_group = cmd.sort_group
      
      p.epilog += "\n  "
      if len(name) > 1:
       p.epilog += "{%s}" % ", ".join(name)
      else:
       p.epilog += name[0]
      if cmd.usage:
       p.epilog += " " + cmd.usage
      if cmd.description:
       if callable(cmd.description):
        p.epilog += "\n    " + cmd.description(name[0])
       else:
        p.epilog += "\n    " + cmd.description
      elif cmd.__doc__:
       p.epilog += "\n    " + cmd.__doc__.split("\n", 1)[0]
      n += 1
  return p.parse_known_args
 
 def main(self, cli):
  if cli._CLI__output_format is None:
   if self.options.robot not in self.__robot_easter_egg_triggers:
    cli._CLI__output_format = self.options.robot

  if self.easter_eggs:
   if self.options.robot.lower() in self.__robot_easter_egg_triggers:
    self.__use_real_output_format = True
    yield output.normal("I AM ROBOT")
    yield output.normal("HEAR ME ROAR")
    raise StopIteration(0)
   if self.options.hep:
    self.__use_real_output_format = True
    yield output.normal("Hep!  Hep!  I'm covered in sawlder! ... Eh?  Nobody comes.")
    yield output.normal("--Red Green, https://www.youtube.com/watch?v=qVeQWtVzkAQ#t=6m27s")
    raise StopIteration(0)
  
  null = getattr(self.options, "null", False)
  ps1 = getattr(self.options, "ps1", "")
  self.__use_real_output_format = False
  try:
   ps1 = "\0" if null else ps1
   
   one_command = False
   if self.extra:
    if not (len(self.extra) and self.extra[0] in self.names):
     # running another command
     one_command = self.extra
    elif not self.__is_shell:
     # running a shell
     debug("re-invoking with __is_shell = True")
     cmd = cli.commands[self.extra[0]](cli)
     cmd.__is_shell = True
     yield cmd.generate_output(self.argv)
     raise StopIteration(127)
   elif self.argv[0] == "":
    # invoked as top-level command
    one_command = []

   if self.options.help:
    if len(self.extra) and self.extra[0] in self.names:
     yield self.do_help(cli, self.extra[0])
    elif one_command == False or len(one_command) == 0:
     yield self.do_help(cli, "")
    else:
     one_command = ["--help"] + one_command
   
   build = ""
   real_command = None
   while True:
    real_command = True
    try:
     if one_command == False:
      if null:
       sys.stdout.write("\0")
       sys.stdout.flush()
       line = array.array('c')
       while True:
        char = sys.stdin.read(1)
        if char == "":
         raise EOFError()
        elif char != "\0":
         line.fromstring(char)
        else:
         break
       line = line.tostring()
      else:
       line = raw_input(ps1 if not build else "")
     if one_command != False:
      argv = one_command
     elif self.real_output_format == "plist":
      if self.options.null:
       argv = plistlib.readPlistFromString(line)
      else:
       build += line + "\n"
       if "</plist>" in line:
        argv = plistlib.readPlistFromString(build)
        build = ""
       else:
        continue
     elif self.real_output_format == "json":
      argv = json.loads(line)
     else:
      argv = shlex.split(line)
     if len(argv):
      if argv[0] == "exit":
       raise StopIteration(0)
      if argv[0] in ("help", "-h", "--help"):
       real_command = False
       yield output.normal(self.help_string(cli, ""))
      if self.easter_eggs and argv[0] in ("hep", "--hep"):
       argv[0] = "--hep"
       argv = ["sh"] + argv
     elif one_command == False:
      continue
     r = 127
     if real_command:
      r = cli.start(argv)
     if one_command != False:
      if real_command:
       raise StopIteration(r)
      else:
       raise StopIteration(0)
    except EOFError:
     raise StopIteration(0)
     break
    except StopIteration:
     raise
    except Exception, exc:
     tb = traceback.format_exc()
     try:
      output.OutputCommand(cli).run([self.argv[0], "127", "", "", tb])
     except:
      pass
     if one_command != False:
      raise StopIteration(127)
   raise StopIteration(0)
  except StopIteration:
   raise
 
 def do_help(self, cli, argv0=None):
  self.__use_real_output_format = True
  try:
   yield output.normal(self.help_string(cli, argv0))
   raise StopIteration(0)
  except CLIError, exc:
   message = "%s: error: %s" % (cli.program, str(exc))
   yield output.error(message)
   raise StopIteration(2)
 
 def help_string(self, cli, argv0=None):
  cmd_name = argv0 or (self.argv[0] if self.argv else "")
  cmd = self.__class__(cli)
  cmd.argv = [cmd_name, "--help"]
  cmd.__is_shell = self.__is_shell and argv0
  if cmd.__is_shell:
   cmd.usage = None
  for i in cmd._parse_args(cli):
   pass
  if cmd.__is_shell:
   cmd.arg_parser.description = cmd.__doc__
  return cmd.arg_parser.format_help()

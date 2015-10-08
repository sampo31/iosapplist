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

# shell command

from __future__ import with_statement

import argparse
import array
import errno
import math
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


def sign(n):
 if n < 0:
  return -1
 if n > 0:
  return +1
 return 0


class ShellCommand(Command):
 """Starts an interactive shell."""
 
 names = ["shell", "sh"]
 add_help = False
 sort_group = -2.2
 usage = "[options [...]] [command [args [...]]]"
 
 __is_shell = True
 __want_help = False
 
 __robot_easter_egg_triggers = ("true", "yes", "on", "y", "1")
 __use_real_output_format = True
 
 @property
 def output_format(self):
  return self.real_output_format if self.__use_real_output_format else ""
 
 def add_args(self, p, cli):
  if not self.__is_shell:
   p.usage = self.usage
   p.description = cli.description
  if self.__is_shell or self.__want_help:
   p.add_argument("--help", "-h", action="store_true",
                  help='show this help and exit')
   if self.easter_eggs:
    p.add_argument("--hep", action="store_true", help=argparse.SUPPRESS)
  if self.__want_help and not self.__is_shell and getattr(cli, "version", None):
   p.add_argument("--version", "-V", action="store_true",
                  help="show program's version number and exit")
  if self.__is_shell:
   p.add_argument("--ps1", default="> ",
                  help='The string to use to prompt for shell input ("> " by'
                       ' default).  -0 supersedes this option.')
   p.add_argument("-0", "--null", action="store_true",
                  help='Prompt for and terminate shell input with a null byte'
                       ' instead of, respectively, ps1 and a newline.  Useful'
                       ' in conjunction with --robot.')
   p.add_argument("--tracebacks-to-stderr", action="store_true",
                  help='Also echo tracebacks to standard error.')
  p.add_argument("--robot", default="", metavar='<format>',
                 help='Produce output suitable for robots.'
                      '  Format should be "plist" or "json".')
  p.formatter_class = argparse.RawDescriptionHelpFormatter
  if not self.__is_shell and self.__want_help:
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
      if n and sign(cmd.sort_group or 1) != sign(sort_group or 1):
        p.epilog += "\n"
      elif n and abs(cmd.sort_group - sort_group) > 1:
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
   # robot
   if self.options.robot.lower() in self.__robot_easter_egg_triggers:
    self.__use_real_output_format = True
    yield output.normal("I AM ROBOT")
    yield output.normal("HEAR ME ROAR")
    raise StopIteration(0)
   # hep
   want_hep = getattr(self.options, "hep", False) # never true if not __is_shell
   want_hep = want_hep or (len(self.extra) == 1 and self.extra[0] == "--hep")
   if want_hep:
    self.__use_real_output_format = True
    yield output.normal("Hep!  Hep!  I'm covered in sawlder! ... Eh?  Nobody comes.")
    yield output.normal("--Red Green, https://www.youtube.com/watch?v=qVeQWtVzkAQ#t=6m27s")
    raise StopIteration(0)
  
  null = getattr(self.options, "null", False)
  ps1 = getattr(self.options, "ps1", "")
  tracebacks_to_stderr = getattr(self.options, "tracebacks_to_stderr", False)
  self.__use_real_output_format = False
  try:
   ps1 = "\0" if null else ps1
   
   one_command = self.extra if len(self.extra) else False
   if not self.__is_shell and not one_command:
    # invoked as top-level command
    one_command = []
   
   help_flag = getattr(self.options, "help", False)
   help_arg = len(self.extra) and self.extra[0] in ("-h", "--help")
   if help_flag or (help_arg and not self.__is_shell):
    yield self.do_help(cli)
   
   if not self.__is_shell:
    if len(self.extra) and self.extra[0] in ("-V", "--version"):
     yield output.normal(self.version_string(cli))
     raise StopIteration(0)
   
   build = ""
   real_command = None
   while True:
    real_command = True
    try:
     if one_command == False:
      try:
       if null:
        self.stdout.write("\0")
        self.stdout.flush()
        line = array.array('c')
        while True:
         char = self.stdin.read(1)
         if char == "":
          raise EOFError()
         elif char != "\0":
          line.fromstring(char)
         else:
          break
        line = line.tostring()
       else:
        self.stdout.write(ps1 if not build else "")
        self.stdout.flush()
        if self.stdin == sys.stdin:
         line = raw_input()
        else:
         line = self.stdin.readline()
         if line.endswith("\n"):
          line = line[:-1]
      except EOFError:
       raise
      except:
       one_command = True  # make the main loop break
       raise
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
     elif self.real_output_format in ("json", "python-repr"):
      argv = json.loads(line)
     else:
      argv = shlex.split(line)
     if len(argv) == 1 and self.__is_shell:
      if argv[0] not in cli.commands:
       if one_command == False:
        if argv[0] == "exit":
         raise StopIteration(0)
       if argv[0] == "help":
        real_command = False
        message = self.help_string(cli, True)
        self.cmd(output.OutputCommand).run([self.argv[0], "0", message])
       if self.easter_eggs and argv[0] == "hep":
        argv[0] = "--hep"
        argv = ["sh"] + argv
       if argv[0] == "version":
        real_command = False
        message = self.version_string(cli)
        self.cmd(output.OutputCommand).run([self.argv[0], "0", message])
     elif not len(argv) and one_command == False:
      continue
     r = 127
     if real_command:
      r, cmd = cli.start(argv, self, default=(None if self.__is_shell else None.__class__),
                         verbose_return=True)
      if tracebacks_to_stderr and cmd.robot_output:
       tbs = cmd.robot_output.get("output", {}).get("traceback", [])
       if tbs:
        for i in tbs:
         print >> self.stderr, i
     if one_command != False:
      if real_command:
       raise StopIteration(r)
      else:
       raise StopIteration(0)
    except EOFError:
     raise StopIteration(0)
     break
    except CLIError, exc:
     message = self.format_cli_error(cli, exc)
     self.cmd(output.OutputCommand).run([self.argv[0], "2", "", message])
     if one_command != False:
      raise StopIteration(2)
    except StopIteration:
     raise
    except Exception, exc:
     if isinstance(exc, IOError) and exc.errno == errno.EPIPE:
      raise StopIteration(0)
      break
     tb = traceback.format_exc()
     try:
      self.cmd(output.OutputCommand).run([self.argv[0], "127", "", "", tb])
     except:
      pass
     if tracebacks_to_stderr:
      print >> self.stderr, tb
     if one_command != False:
      raise StopIteration(127)
   raise StopIteration(0)
  except CLIError, exc:
   yield output.error(self.format_cli_error(cli, exc))
   raise StopIteration(2)
  except StopIteration:
   raise
 
 def cmd(self, x):
  if isinstance(x, basestring):
   x = self.cli.commands[x]
  if issubclass(x, Command):
   x = x(self.cli)
   x.stdin = self.stdin
   x.stdout = self.stdout
   x.stderr = self.stderr
  return x
 
 def format_cli_error(self, cli, exc):
  argv0 = self.argv[0] if self.__is_shell else cli.program
  return "%s: error: %s" % (argv0 or self.names[0], str(exc))

 def do_help(self, cli, for_program=None):
  self.__use_real_output_format = True
  try:
   yield output.normal(self.help_string(cli, for_program))
   raise StopIteration(0)
  except CLIError, exc:
   yield output.error(self.format_cli_error(cli, exc))
   raise StopIteration(2)
 
 def help_string(self, cli, for_program=None):
  if for_program is None:
   for_program = not self.__is_shell
  cmd = self.__class__(cli)
  cmd.argv = [self.argv[0], "--help"]
  cmd.__is_shell = not for_program
  cmd.__want_help = True
  for i in cmd._parse_args(cli):
   pass
  return cmd.arg_parser.format_help()
 
 def version_string(self, cli):
  return "%s %s" % (str(cli.program), str(cli.version))

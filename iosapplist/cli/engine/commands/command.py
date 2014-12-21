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

# command command

from __future__ import with_statement

import argparse
import re
import sys

from .. import Command, output


__all__ = ["CommandCommand"]


class CommandCommand(Command):
 """Runs a command."""
 
 add_help = False
 description = None
 easter_eggs = False
 names = ["command", "cmd"]
 sort_group = float("-inf")
 usage = "[options [...]] [command [args [...]]]"
 want_help = False
 
 __is_easter_egg = False
 __robot_easter_egg_triggers = ("true", "yes", "on", "y", "1")

 @property
 def output_format(self):
  options = getattr(self, "options", None)
  if getattr(options, "help", False) or self.__is_easter_egg:
   cmd_name = self.extra[0] if self.extra else None
   if not (cmd_name and cmd_name not in self.names):
    robot = getattr(options, "robot", "")
    if robot not in self.__robot_easter_egg_triggers:
     return robot
    else:
     return self.real_output_format
  return ""
 
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
  p.formatter_class = argparse.RawDescriptionHelpFormatter
  if self.want_help:
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
    self.__is_easter_egg = True
    yield output.normal("I AM ROBOT")
    yield output.normal("HEAR ME ROAR")
    yield output.stop(0)
   if self.options.hep:
    self.__is_easter_egg = True
    yield output.normal("Hep!  Hep!  I'm covered in sawlder! ... Eh?  Nobody comes.")
    yield output.normal("--Red Green, https://www.youtube.com/watch?v=qVeQWtVzkAQ#t=6m27s")
    yield output.stop(0)
  
  if self.options.help:
   cmd_name = self.extra[0] if self.extra else None
   if cmd_name and cmd_name not in self.names:
    cmd = cli.commands.get(cmd_name, None)
    if cmd:
     if cmd.add_args:
      yield output.stop(cli([cmd_name, "--help"]))
     else:
      usage = "usage: %s %s" % (cli.program, cmd_name)
      if cmd.usage:
       usage += " " + cmd.usage
      description = None
      if cmd.description:
       if callable(cmd.description):
        description = cmd.description(cmd.argv[0])
       else:
        description = cmd.description
      if not description:
       description = cmd.__doc__
      if description:
       usage += "\n\n" + description
      usage += "\n"
      output.OutputCommand(cli).run([self.argv[0], "0", usage])
      yield output.stop(0)
    else:
     message = "%s is not a valid command" % cmd_name
     output.OutputCommand(cli).run([self.argv[0], "2", "", message])
     yield output.stop(2)
   else:
    cmd = self.__class__(cli)
    cmd.argv = [cmd_name, "--help"]
    cmd.want_help = True
    for i in cmd._parse_args(cli):
     pass
    if cmd_name in self.names:
     self.arg_parser.description = cmd.__doc__
    yield output.normal(cmd.arg_parser.format_help())
    yield output.stop(0)
  else:
   yield output.stop(cli(self.extra))

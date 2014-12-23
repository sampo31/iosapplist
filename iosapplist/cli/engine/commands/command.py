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
from ..cli import CLIError


__all__ = ["CommandCommand"]


class CommandCommand(Command):
 """Runs a command."""
 
 names = ["command", "cmd"]
 add_help = False
 easter_eggs = False
 sort_group = float("-inf")
 usage = "[options [...]] [command [args [...]]]"
 want_help = False
 
 __use_real_output_format = True
 
 @property
 def output_format(self):
  return self.real_output_format if self.__use_real_output_format else ""
 
 def add_args(self, p, cli):
  if self.want_help:
   p.add_argument("--help", "-h", action="store_true",
                  help='show this help message and exit')
  return p.parse_known_args
 
 def main(self, cli):
  if len(self.args) == 1:
   arg = self.args[0]
   if self.easter_eggs and arg == "hep":
    self.__use_real_output_format = True
    yield output.normal("Hep!  Hep!  I'm covered in sawlder! ... Eh?  Nobody comes.")
    yield output.normal("--Red Green, https://www.youtube.com/watch?v=qVeQWtVzkAQ#t=6m27s")
    raise StopIteration(0)
   if arg in ("-h", "--help"):
    self.__use_real_output_format = True
    try:
     cmd_name = self.argv[0] if self.argv else ""
     cmd = self.__class__(cli)
     cmd.argv = [cmd_name, "--help"]
     cmd.want_help = cmd_name not in self.names
     for i in cmd._parse_args(cli):
      pass
     if cmd_name in self.names:
      cmd.arg_parser.description = cmd.__doc__
     yield output.normal(cmd.arg_parser.format_help())
     raise StopIteration(0)
    except CLIError, exc:
     message = "%s: error: %s" % (cli.program, str(exc))
     yield output.error(message)
     raise StopIteration(2)
  
  try:
   cmd_name = self.extra[0] if self.extra else None
   self.argv[0] = cmd_name or self.argv[0]
   yield cli(self.extra)
  except CLIError, exc:
   message = "%s: error: %s" % (cli.program, str(exc))
   yield output.error(message)
   raise StopIteration(2)

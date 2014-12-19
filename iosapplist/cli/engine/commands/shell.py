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

import plistlib
import readline
import shlex
import traceback

try:
 import json
except ImportError:
 import simplejson as json

from .. import Command, output


__all__ = ["ShellCommand"]


class ShellCommand(Command):
 """Starts an interactive shell."""
 names = ["shell", "sh"]
 sort_group = -3
 usage = "[command [args [...]]]"
 add_args = False

 @property
 def output_format(self):
  return ""
 
 def main(self, cli):
  if self.argv[1:]:
   yield output.stop(cli(["command"] + self.argv[1:]))
  else:
   build = ""
   while True:
    try:
     line = raw_input("> " if not build else ". ")
     if self.real_output_format == "plist":
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
       yield output.stop(0)
       raise StopIteration()
      if argv[0] == "help":
       argv[0] = "--help"
     cli(["command", "--robot=" + self.real_output_format] + argv)
    except EOFError:
     yield output.stop(0)
    except StopIteration:
     raise
    except Exception, exc:
     output.OutputCommand(cli).run(["shell", "127", "", traceback.format_exc(exc)])
   yield output.stop(0)

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

# python-repl command

from __future__ import with_statement

import code
import sys

from .. import Command, output


__all__ = ["PythonReplCommand"]


class PythonReplCommand(Command):
 """Starts an interactive Python prompt with access to an app_list object."""
 names = ["python", "py", "python-repl"]
 preamble = ""
 ps1 = getattr(sys, "ps1", None) or ">>> "
 sort_group = -2

 def add_args(self, p, cli):
  return
 
 def main(self, cli):
  def _console_banner():
   banner = []
   dummy_console = code.InteractiveConsole()
   def dummy_write(data):
    banner.append(data)
   dummy_console.write = dummy_write
   def dummy_input(prompt):
    raise EOFError()
   dummy_console.raw_input = dummy_input
   dummy_console.interact()
   return "\n".join("".join(banner).rstrip().splitlines()[:-1])
  scope  = dict([(attr, getattr(cli, attr)) for attr in dir(cli)
                 if not attr.startswith("_")])
  ps1    = getattr(sys, "ps1", None) or ">>> "
  banner = _console_banner()
  if self.preamble:
   banner += "\n"
   banner += self.preamble
  scope["__builtins__"] = __builtins__
  code.interact(banner, None, scope)
  raise StopIteration(0)

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

# iosapplist CLI __init__.py file
# (No shit, Sherlock.)

"""A command-line utility to list iOS App Store apps."""


from __future__ import with_statement

import types

from ..app import App
from ..applist import AppList
from ..container import ContainerRoot
from .. import __version__ as pkg_version

from engine import CLI, CLIError, Command, output, debug


__all__  = ["CLI", "CLIError", "Command", "output"]
__all__ += ["ShellCommand", "main"]  # imported at the bottom of the file


class CLI(CLI):
 default_command = "ls"
 description = __doc__
 easter_eggs = True
 program = "iosapplist"
 version = pkg_version
 
 app_class = App
 app_root  = None
 
 __app_list = None
 @property
 def app_list(self):
  if not self.__app_list:
   root = ContainerRoot(self.app_root or "/var/mobile")
   self.__app_list = AppList(root=root)
   self.app_root = self.__app_list.root.path
  return self.__app_list

import commands
CLI.commands.register(commands)


from commands.shell import ShellCommand

from __main__ import main

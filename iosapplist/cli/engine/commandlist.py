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

# CommandList class

from __future__ import with_statement

import pkgutil
import types

from command import Command


__all__ = ["CommandList"]


class CommandList(object):
 __commands_dict = dict
 
 def __init__(self):
  self.__commands_dict = {}
 
 def __contains__(self, item): return self.__commands_dict.__contains__(item)
 def  __getitem__(self, item): return self.__commands_dict.__getitem__(item)
 def          get(self, k, d): return self.__commands_dict.get(k, d)
 def        items(self      ): return self.__commands_dict.items()
 def         keys(self      ): return self.__commands_dict.keys()
 def       values(self      ): return self.__commands_dict.values()
 def    iteritems(self      ): return self.__commands_dict.iteritems()
 def     iterkeys(self      ): return self.__commands_dict.iterkeys()
 def   itervalues(self      ): return self.__commands_dict.itervalues()
 def    viewitems(self      ): return self.__commands_dict.viewitems()
 def     viewkeys(self      ): return self.__commands_dict.viewkeys()
 def   viewvalues(self      ): return self.__commands_dict.viewvalues()
 
 def __iter__(self):
  return sorted(set(self.__commands_dict.itervalues())).__iter__()
 
 def copy(self):
  new = CommandList()
  new.__commands_dict = self.__commands_dict.copy()
  return new
 
 def register(self, item):
  def register_one(cmd):
   for name in cmd.names:
    self.__commands_dict[name] = cmd
  
  if isinstance(item, type) and issubclass(item, Command):
   register_one(item)
  elif isinstance(item, (list, tuple)):
   for cmd in item:
    register_one(cmd)
  elif isinstance(item, types.ModuleType):
   modules = [item]
   path, name = item.__path__, item.__name__
   for importer, module_name, is_package in pkgutil.iter_modules(path, name + "."):
    modules += [importer.find_module(module_name).load_module(module_name)]
   for module in modules:
    for i in dir(module):
     cmd = getattr(module, i, None)
     if isinstance(cmd, type) and issubclass(cmd, Command) and cmd is not Command:
      register_one(cmd)
  else:
   raise TypeError("argument must be a Command subclass, list, tuple, or module")

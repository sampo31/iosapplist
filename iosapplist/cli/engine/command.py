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

# Command class

from __future__ import with_statement

import argparse
import plistlib
import re
import string
import sys

try:
 import json
except ImportError:
 import simplejson as json

from ...util import safe_print

import output


__all__ = ["Command", "output"]


class Template(string.Template):
 idpattern = r"[-._a-z][-._a-z0-9]*"


class Command(object):
 """The base type for commands."""
 
 class __meta(type):
  def __new__(mcs, name, bases, dict):
   cls = type.__new__(mcs, name, bases, dict)
   if not isinstance(cls.names, (list, tuple)):
    raise TypeError("names attribute must be a list or tuple")
   if not cls.__doc__:
    for c in cls.__mro__:
     if c.__doc__:
      cls.__doc__ = c.__doc__
      break
   return cls
  
  __sort_group_key = None
  @property
  def _sort_group_key(cls):
   if cls.__sort_group_key == None or cls.__sort_group_key[1] != cls.sort_group:
    if cls.sort_group >= 0:
     if cls.sort_group == float("inf"):
      key = sys.maxint
     else:
      key = cls.sort_group
    else:
     if cls.sort_group == float("-inf"):
      key = sys.maxint * 2
     else:
      key = sys.maxint * 2 + cls.sort_group
    cls.__sort_group_key = (key, cls.sort_group)
   return cls.__sort_group_key[0]
  
  __sort_name = None
  @property
  def _sort_name(cls):
   if cls.__sort_name == None or cls.__sort_name[1] != cls.names[0]:
    cls.__sort_name = (cls.names[0].lower(), cls.names[0])
   return cls.__sort_name[0]
  
  @property
  def _sort_key(cls):
   return (cls._sort_group_key, cls._sort_name)
  
  def __ge__(cls, other): return cls._sort_key >= other._sort_key
  def __gt__(cls, other): return cls._sort_key >  other._sort_key
  def __le__(cls, other): return cls._sort_key <= other._sort_key
  def __lt__(cls, other): return cls._sort_key <  other._sort_key
  def __eq__(cls, other): return cls._sort_key == other._sort_key
  def __ne__(cls, other): return cls._sort_key != other._sort_key
 __metaclass__ = __meta
 
 add_help = True
 names = []
 names_are_aliases = True
 description = None
 show_in_help = True
 sort_group = 0
 usage = None
 
 def __init__(self, cli):
  self.return_code = None
  self.stdin  = sys.stdin
  self.stdout = sys.stdout
  self.stderr = sys.stderr
  self.cli    = cli
 
 def add_args(self, arg_parser, cli):
  raise TypeError("Command.add_args is an abstract method")
 
 def main(self, cli):
  raise TypeError("Command.main is an abstract method")
 
 @property
 def is_robot(self):
  return self.output_format == "human" or bool(self.output_format)
 
 @property
 def output_format(self):
  return self.real_output_format
 
 @property
 def real_output_format(self):
  return self.cli._CLI__output_format or ""
 
 def run(self, argv=[], return_output=False):
  if self.return_code is not None:
   raise RuntimeError("this instance has already been executed")
  
  self.argv = argv
  self.args = argv[1:]
  
  human_output = {"normal": self.stdout, "error": self.stderr}
  robot_output = dict(cmd=self.argv[0], success=None, return_code=None,
                      output={"normal": [], "error": []})
  
  for output_generator in (self._parse_args, self.main):
   output_iterator = output_generator(self.cli)
   for item in output_iterator:
    value = item.value
    if item.type == "stop":
     self.return_code = item.value
     break
    if self.is_robot or return_output:
     robot_output["output"][item.type] += [value]
    else:
     if isinstance(value, dict):
      if isinstance(item.human, basestring):
       value = Template(item.human).safe_substitute(value)
     safe_print(value, human_output[item.type])
    if self.return_code != None and not isinstance(output_iterator, (list, tuple)):
     break
   if self.return_code != None:
    break
  
  if self.return_code is None:
   self.return_code = 127
  
  if self.is_robot or return_output:
   robot_output["return_code"] = self.return_code
   robot_output["success"] = self.return_code == 0
   if not return_output:
    if self.output_format == "plist":
     print >> self.stdout, plistlib.writePlistToString(robot_output)
    elif self.output_format == "json":
     print >> self.stdout, json.dumps(robot_output)
    else:
     raise ValueError("bad output format %s" % repr(self.output_format))
  
  return robot_output if return_output else self.return_code

 def _parse_args(self, cli):
  out = []
  r = None
  if callable(self.add_args):
   self.arg_parser = p = argparse.ArgumentParser(self.argv[0], add_help=self.add_help)
   parse_function = self.add_args(p, cli) or p.parse_args
   if not p.usage:
    if self.usage:
     usage = self.argv[0] + " " + self.usage
    else:
     usage = re.sub("^usage: ", "", p.format_usage())
    p.usage = usage
   if isinstance(p.usage, basestring):
    p.usage = cli.program + " " + p.usage
   if not p.description:
    p.description = self.__doc__
   def _print_message(message, file=None, _out=out):
    if file == sys.stdout:
     _out += [output.normal(message)]
    else:
     _out += [output.error(message)]
   p._print_message = _print_message
   try:
    self.options = parse_function(self.args)
    if parse_function == p.parse_known_args:
     self.options, self.extra = self.options
   except SystemExit, exc:
    r = exc.code
  
  for item in out:
   yield item
  if r != None:
   yield output.stop(r)

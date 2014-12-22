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

# list command

from __future__ import with_statement

from .. import Command, output, debug


__all__ = ["ListCommand"]


class ListCommand(Command):
 """Shows information about one or more App Store apps (all apps by default)."""
 names = ["list", "ls"]
 usage = "[-l/--long] [--[list-]keys] [--<key>] [<bundle-id-or-uuid> [...]]"
 
 def add_args(self, p, cli):
  p.add_argument("-l", "--long", action="store_true",
                 help="""List more information about each app.""")
  p.add_argument("--list-keys", "--keys", action="store_true", dest="list_keys",
                 help="""Show a list of valid information keys.""")
  return p.parse_known_args
 
 def main(self, cli):
  def list_keys():
   debug("making list of keys")
   keys = sorted(cli.app_list.app_class.slot_names().keys())
   keys = list(keys)
   return keys
  
  if self.options.list_keys:
   # list available keys
   debug("listing available keys")
   keys = list_keys()
   if self.is_robot:
    yield output.normal(keys)
   else:
    for k in keys:
     yield output.normal(k.replace("_", "-"))
  else:
   # find apps
   key = None
   search = self.extra
   if len(self.extra):
    if self.extra[0].startswith("--"):
     key = self.extra[0][2:]
     search = self.extra[1:]
   
   if key:
    # sanitize the requested key
    if not self.is_robot:
     key = key.replace("-", "_")
    keys = list_keys()
    if key not in keys:
     yield output.error("invalid key %s" % repr(key))
     raise StopIteration(2)
 
   if not cli.app_list:
    debug("populating the app list cache")
    cli.app_list.find_all()
   if search:
    # search for some apps
    debug("listing some apps")
    results = [(query, cli.app_list.get(query, None)) for query in search]
    n_matches = 0
    for query, match in results:
     if not match:
      yield output.error("could not find an app that matches %s" % repr(query))
      if not self.is_robot:
       yield output.error("")
     else:
      n_matches += 1
    if not n_matches:
     raise StopIteration(1)
    app_list = (match for query, match in results if match)
   else:
    # show all apps
    debug("listing all apps")
    app_list = cli.app_list.sorted()
   
   debug("outputting the list")
   for app in app_list:
    # show the apps
    if app == None:
     continue
    if key:
     # show one key
     try:
      yield output.normal(app[key])
     except KeyError:
      yield output.error("invalid key %s" % repr(key))
      raise StopIteration(2)
    else:
     if self.is_robot:
      yield output.normal(dict(app))
     else:
      yield output.normal(app.info_str(self.options.long))
   
   raise StopIteration(0)

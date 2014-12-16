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

# Command-line interface

"""A command-line utility to list iOS App Store apps."""

usage = """Usage: iosapplist [options] command [args]

List iOS App Store apps.

Options:
 -j / --json        Output (and shell input) should be a JSON document.
 -p / --plist       Output (and shell input) should be an XML property list.
 --root             The path to the directory containing app containers or
                    a mobile home directory (defaults to "/var/mobile").

Commands:
 -h / --help        Display this help information and exit.
 list [<app>]       Shows information about one or more App Store apps (all apps
                    if <app> is omitted).
 get <key> [<app>]  Show a specific property key for one or more App Store apps.
                    Use -h / --help / -k / --keys / ? / help as the key for a
                    list of keys.
 shell              Start an interactive shell.
 python-repl        Start an interactive Python prompt with an applist object.

Arguments for all commands:
 -a / --all         Perform the specified action on all App Store apps (not
                    needed for list).
 -u / --uuid        A UUID is given as <app> instead of a bundle ID.
 <app>              The bundle IDs (or UUIDs if -u / --uuid is set) for each app
                    you want to work with.
 -v / --verbose     Show more information for each app (implied when <app> is
                    given.)"""

import code
import os
import plistlib
import readline
import shlex
import sys
import traceback
import types

from string import Template

try:
 import json
except ImportError:
 import simplejson as json

from applist import *
from container import ContainerRoot
from util import *

app_info_keys = ("friendly", "bundle_id", "bundle_uuid", "data_uuid",
                 "bundle_path", "data_path", "useable", "found")
def app_info(app, human_readable=False, verbose=True, found_key=True):
 info = dict(friendly=app.friendly, bundle_id=app.bundle_id,
             bundle_uuid=app.containers.bundle.uuid,
             data_uuid=app.containers.data.uuid,
             useable=app.useable)
 if verbose or human_readable:
  info["bundle_path"] = app.containers.bundle.path
  info["data_path"] = app.containers.data.path
 if found_key:
  info["found"] = True
 if human_readable:
  info["useable"] = "Yes" if info["useable"] else "No"
  tpl = u"""$friendly ($bundle_id):
    Bundle container path:  $bundle_path
    Bundle container UUID:  $bundle_uuid
      Data container path:  $data_path
      Data container UUID:  $data_uuid
                  Useable:  $useable"""
  return Template(tpl).substitute(info)
 else:
  return info

def fmt_result(mode, cmd, success=False, exit_code=0, data=None, **kwargs):
 d = dict(cmd=cmd, success=success, exit_code=exit_code, data=data, **kwargs)
 if mode == "json":
  return json.dumps(d)
 elif mode == "plist":
  return plistlib.writePlistToString(d)
 else:
  raise ValueError("mode must be one of json or plist, not %s." % repr(mode))

def main(argv=sys.argv):
 prog = argv[0]
 if len(argv) < 2:
  safe_print(usage)
  return 2
 opts, cmd, args = parse_argv(argv[1:])
 if "h" in opts or "help" in opts:
  safe_print(usage)
  return 0
 use_json = "j" in opts or "json" in opts
 use_plist = "p" in opts or "plist" in opts
 out_mode = ("json" if use_json else "plist") if use_json or use_plist else ""
 root = ContainerRoot(opts.get("root", "/var/mobile"))
 if use_json and use_plist:
  safe_print("Please choose only one or neither of -j / --json or -p /"
             " --plist.")
  return 2
 applist = AppList(root=root)
 return run_cmd(cmd, args, applist, out_mode)

def shell(args, applist, out_mode):
 build = ""
 while True:
  try:
   line = raw_input(">>> " if not build else "... ")
   if out_mode == "plist":
    build += line + "\n"
    if "</plist>" in line:
     _, cmd, args = parse_argv(plistlib.readPlistFromString(build))
     build = ""
    else:
     continue
   elif out_mode == "json":
    _, cmd, args = parse_argv(json.loads(line))
   else:
    _, cmd, args = parse_argv(shlex.split(line))
   if cmd == "exit":
    return 0
   run_cmd(cmd, args, applist, out_mode)
  except EOFError:
   return 0
  except Exception, exc:
   traceback.print_exc(exc)
 return 0

def python_repl(args, applist):
 def _make_scope():
  src_scope = globals()
  scope = dict([(k, src_scope[k]) for k in src_scope
                if (not (k.startswith("_") and k not in "__doc__") and
                    not k in ("decimal", "inject", "main") and
                    not isinstance(src_scope[k],types.ModuleType))])
  scope["__builtins__"] = __builtins__
  return scope
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
  return "\n".join("".join(banner).rstrip().splitlines()[:-1]) + "\n"
 scope  = _make_scope()
 ps1    = getattr(sys, "ps1", None) or ">>> "
 usage  = ps1 + "applist = AppList(root=%s)\n" % repr(applist.root.path)
 banner = "\n".join((_console_banner(), usage))
 scope["applist"] = applist
 code.interact(banner, None, scope)
 return 0

def run_cmd(cmd, args, applist, out_mode):
 if cmd == "shell":
  return shell(args, applist, out_mode)
 if cmd == "python-repl":
  return python_repl(args, applist)
 if (cmd == "list" and
     "v" not in args and "verbose" not in args and not len(args[""])):
  # List App Store apps
  apps = applist.find_all().sorted()
  if out_mode:
   data = [app_info(app, verbose=False, found_key=False) for app in apps]
   print fmt_result(out_mode, cmd, True, data=data)
  else:
   for i in apps:
    if not i.useable: info = "(not useable)"
    safe_print(u"%s (%s)" % (i.friendly, (i.bundle_id if i.useable else i)))
  return 0
 elif cmd == "get":
  use_uuid = "u" in args or "uuid" in args or ("g" in args or "guid" in args)
  all_apps = not len(args[""]) or "a" in args or "all" in args
  apps = args[""]
  key, apps = apps[0] if len(apps) else "", apps[1:]
  if not out_mode: key = key.replace("-", "_")
  success = True
  data = []
  help_mode = "h" in args or "help" in args or key in ("help", "?")
  help_mode = help_mode or "k" in args or "keys" in args
  if help_mode:
   if out_mode: data = app_info_keys[:]
   else:
    for i in sorted(app_info_keys):
     safe_print(i.replace("_", "-"))
  else:
   if not len(apps) and not all_apps:
    error = "Please specify one or more apps, or set -a / --all."
    if out_mode: print fmt_result(out_mode, cmd, False, 2, data=error)
    else: safe_print(error)
    return 2
   elif not key:
    error = "Please specify a key, or use -h / --help / -k / --keys for a list."
    if out_mode: print fmt_result(out_mode, cmd, False, 2, data=error)
    else: safe_print(error)
    return 2
   try:
    if all_apps:
     # List all apps
     apps = applist.find_all().sorted()
     for app in apps:
      info = app_info(app, verbose=True)[key]
      if out_mode: data += [info]
      else: safe_print(info)
    else:
     # List some apps
     search_mode = "uuid" if use_uuid else "bundle_id"
     for i in apps:
      app = applist.find(i, search_mode)
      if app:
       info = app_info(app, verbose=True)[key]
       if out_mode: data += [info]
       else: safe_print(info)
      else:
       success = False
       if out_mode: data += [dict(name=i, found=False)]
       else: safe_print("Could not find app %s.\n" % repr(i))
   except KeyError:
    error = "%s is not a valid key.  Use -h / --help / -k / --keys for a list."
    error = error % repr(key)
    if out_mode: print fmt_result(out_mode, cmd, False, 2, data=error)
    else: safe_print(error)
    return 2
  if out_mode: print fmt_result(out_mode, cmd, success, int(not success),
                                data=data)
  return int(not success)
 elif cmd == "list" and ("v" in args or "verbose" in args or len(args[""])):
  # Show verbose app info
  use_uuid = "u" in args or "uuid" in args or ("g" in args or "guid" in args)
  all_apps = not len(args[""]) or "a" in args or "all" in args
  verbose  = "v" in args or "verbose" in args
  apps = args[""]
  success = True
  data = []
  if all_apps:
   # List all apps
   apps = applist.find_all().sorted()
   for app in apps:
    if out_mode: data += [app_info(app, verbose=verbose)]
    else: safe_print(app_info(app, True) + "\n")
  else:
   # List some apps
   search_mode = "uuid" if use_uuid else "bundle_id"
   for i in apps:
    app = applist.find(i, search_mode)
    if app:
     if out_mode: data += [app_info(app, verbose=verbose)]
     else: safe_print(app_info(app, True) + "\n")
    else:
     success = False
     if out_mode: data += [dict(name=i, found=False)]
     else: safe_print("Could not find app %s.\n" % repr(i))
  if out_mode: print fmt_result(out_mode, cmd, success, int(not success),
                                data=data)
  return int(not success)
 else:
  # Invalid command
  error = "%s is not a valid command." % repr(cmd)
  if out_mode: print fmt_result(out_mode, cmd, False, 2, error)
  else: safe_print(error)
  return 2

def parse_argv(argv):
 opts = {}
 cmd = ""
 args = {"": []}
 for i in argv:
  if i.startswith("--"):
   parts = i.lstrip("-").split("=", 1)
   if len(parts) == 1: parts += [True]
   k, v = parts
   (args if cmd else opts)[k] = v
  elif i.startswith("-"):
   for k in i.lstrip("-"):
    (args if cmd else opts)[k] = True
  else:
   if cmd: args[""] += [i]
   else: cmd = i
 return opts, cmd, args

if __name__ == "__main__":
 try:
  sys.exit(main(sys.argv))
 except KeyboardInterrupt:
  pass

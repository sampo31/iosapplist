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

# App class

from __future__ import with_statement

import os
import string

from container import ContainerError, Container, ContainerClass, ContainerRoot
from util import propertylist
from util import *

__all__ = ["AppError", "App"]


class Template(string.Template):
 idpattern = r"[-._a-z][-._a-z0-9]*"


class AppError(Exception): pass


class App(object):
 """Describes an App Store app.

Attributes:
 bundle_id:   the bundle ID of the app
 friendly:    the display name of the app
 containers:
  bundle:     the Container object for the app's bundle container
  data:       the Container object for the app's data container
 bundle_path: alias for containers.bundle.path
 bundle_uuid: alias for containers.bundle.uuid
 data_path:   alias for containers.data.path
 data_uuid:   alias for containers.data.uuid
 name:        the name of the .app folder
 sort_key:    useful for sorting
 useable:     True if the app can be accessed; False otherwise

sort_key is the app's friendly name, converted to lowercase, with diacritical
marks stripped using util.strip_latin_diacritics(), an underscore, and then the
app's bundle ID.
Example:  facebook_com.facebook.Facebook

On iOS <= 7.x, containers.bundle and containers.data will be the same object,
and they will both have the psuedo-ContainerClass LEGACY.

All attributes described above, except for containers, can be accessed in
dictionary style as well as attribute style.

"""
 
 __slots__ = [
  "bundle_id", "name", "friendly", "sort_key", "containers",
  "bundle_path", "bundle_uuid", "data_path", "data_uuid",
  "useable",
  "info_tpl", "__ready", "__dummy"
 ]
 
 info_tpl = u"$friendly ($bundle_id)"
 
 def __nonzero__(self):
  return bool(self.__ready)
 
 @classmethod
 def slot_names(cls):
  """Returns a mapping of attribute names to human-readable descriptions."""
  return dict(
   bundle_id   = "Bundle ID",
   name        = "Bundle name",
   friendly    = "Name",
   sort_key    = "Sort key",
   bundle_path = "Bundle container path",
   bundle_uuid = "Bundle container UUID",
   data_path   = "Data container path",
   data_uuid   = "Data container UUID",
   useable     = "Useable",
  )
 
 def __new__(cls, bundle_container, data_container, *args, **kwargs):
  # This exists to allow AppList.find_all() to not have to use a temporary
  # intermediate object when scanning for apps on iOS >= 8, thus eliminating
  # the need to have to iterate through the cache to make the App objects
  # once the containers are discovered and then replace each cache entry
  # with the App.
  self = super(App, cls).__new__(cls, bundle_container, data_container)
  class containers(object):
   bundle = bundle_container
   data   = data_container
  self.containers = containers = containers()
  self.bundle_id = None
  self.__ready = self.__dummy = False
  return self
 
 def __init__(self, bundle_container, data_container, *args, **kwargs):
  """Loads the app's info.

bundle_container is the Container object or directory of the app's
Bundle container.

data_container is the Container object or directory of the app's
Data container.

On iOS <= 7.x, bundle_container and data_container should be equal to
each other and should have the ContainerClass LEGACY.

"""
  try:
   if not isinstance(bundle_container, Container):
    bundle_container = Container(bundle_container)
   if not isinstance(data_container, Container):
    data_container = Container(data_container)
  except ContainerError, exc:
   raise AppError(exc)
  
  containers = self.containers
  containers.bundle = bundle_container
  containers.data   = data_container
  
  # sanity-check the container(s)
  if containers.bundle.class_ not in (ContainerClass.BUNDLE, ContainerClass.LEGACY):
   if isinstance(containers.bundle.class_, ContainerClass):
    raise AppError("bundle_container must be a bundle or legacy container,"
                   " not a/an %s container" % containers.bundle.class_.name.lower())
   else:
    raise AppError("The Python object for the app's bundle container is malformed.")
  if containers.data.class_ not in (ContainerClass.DATA, ContainerClass.LEGACY):
   if isinstance(containers.data.class_, ContainerClass):
    raise AppError("data_container must be a data or legacy container,"
                   " not a/an %s container" % containers.data.class_.name.lower())
   else:
    raise AppError("The Python object for the app's data container is malformed.")
  if containers.bundle.bundle_id != containers.data.bundle_id:
   raise AppError("The bundle and data containers have different bundle IDs.")
  
  # find the Info.plist file
  info_plist = ""
  for i in os.listdir(containers.bundle.path):
   app_dir = os.path.realpath(os.path.join(containers.bundle.path, i))
   if (os.path.isdir(app_dir) and i.endswith(u".app")):
    self.name = i
    info_plist = os.path.join(app_dir, u"Info.plist")
    break
  if not info_plist: raise AppError("This is not a valid iOS App Store app.")
  
  self.bundle_id = "invalid.appbackup.corrupted"
  self.friendly  = to_unicode(self.name.rsplit(u".app", 1)[0], errors="ignore")
  self.sort_key  = u"%s_%s" % (strip_latin_diacritics(self.friendly.lower()),
                               to_unicode(self.bundle_id, errors="ignore"))
  self.useable   = False
  
  try:
   if os.path.isfile(os.path.realpath(info_plist)):
    pl = propertylist.load(info_plist)
    if "CFBundleIdentifier" in pl:
     self.bundle_id = pl["CFBundleIdentifier"]
     if self.bundle_id != containers.bundle.bundle_id:
      raise AppError("The bundle ID in Info.plist does not match the bundle ID"
	             " of the bundle container.")
     self.friendly  = to_unicode(pl.get("CFBundleDisplayName", "").strip() or
                                 self.name.rsplit(u".app", 1)[0], errors="ignore")
     self.sort_key  = u"%s_%s" % (strip_latin_diacritics(self.friendly.lower()),
                                  to_unicode(self.bundle_id, errors="ignore"))
     self.useable   = True
  except propertylist.PropertyListError:
   pass
  
  self.__ready = True
 
 @property
 def bundle_path(self):
  return self.containers.bundle.path
 
 @property
 def bundle_uuid(self):
  return self.containers.bundle.uuid
 
 @property
 def data_path(self):
  return self.containers.data.path
 
 @property
 def data_uuid(self):
  return self.containers.data.uuid
 
 # Utility methods
 
 def info_str(self, verbose=True):
  info_tpl = self.info_tpl.split(":", 1)[0] if verbose else self.info_tpl
  info = Template(info_tpl).safe_substitute(dict(self))
  if verbose:
   blacklist = ("info_tpl", "bundle_id", "friendly", "sort_key")
   key_names = [key for key in self.iterkeys() if key not in blacklist]
   padding = reversed(sorted([len(name) for name in self.slot_names().values()])).next()
   padding += 2
   info += ":\n"
   for attr, value in self.iteritems():
    if attr not in ("bundle_id", "friendly", "sort_key"):
     name = self.slot_names().get(attr, None)
     if name:
      if len(name) < padding:
       name = ((" " * padding) + name)[-padding:]
      info += u"%s:  %s\n" % (name, to_unicode(value))
  return info
 
 # Dict-alike methods
 
 def __contains__(self, key):
  return key in self.iterkeys()
 
 def __getitem__(self, key):
  return getattr(self, key)

 def items(self):
  return list(self.iteritems())
 
 def iteritems(self):
  types = (basestring, int, long, float, list, tuple, bool, None.__class__)
  blacklist = ("info_tpl",)
  for cls in reversed(self.__class__.__mro__):
   if issubclass(cls, App):
    for attr in cls.__slots__:
     if not attr.startswith("_") and attr not in blacklist:
      value = getattr(self, attr)
      if isinstance(value, types):
       yield (attr, value)
  raise StopIteration
 
 def iterkeys(self):
  for k, v in self.iteritems():
   yield k
  raise StopIteration
 
 def itervalues(self):
  for k, v in self.iteritems():
   yield v
  raise StopIteration
 
 def keys(self):
  return list(self.iterkeys())
 
 def values(self):
  return list(self.itervalues())

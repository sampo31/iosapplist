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

# AppList class

from __future__ import with_statement

import os

from app import AppError, App
from container import ContainerError, Container, ContainerRoot
from util import propertylist
from util import *

__all__ = ["AppListError", "AppList"]


class AppListError(Exception): pass


class AppList(object):
 def __init__(self, root, app_class=App, *args, **kwargs):
  """Creates the app list and builds the cache.

The root can be "/var/mobile", an iOS 8 "Containers" directory, its "Bundle"
or "Data" subdirectories, their "Application" subdirectory, the "Applications"
directory from iOS <= 7.x, or a directory with an eqivalent structure to any
of those (e.g. the "data" directory from an iOS Simulator instance).

app_class is the class to instantiate for each app.  It can be App (the default)
or a subclass of App.  Extra positional or keyword arguments will be passed to
the constructor of app_class each time an app_class instance is made.

"""
  self.root = root if isinstance(root, ContainerRoot) else ContainerRoot(root)
  self.app_class = app_class
  self.app_args = args
  self.app_kwargs = kwargs
  self.__cache = {}
 
 def __list(self):
  if not self:
   return []
  return self.__cache["as_list"]
 
 def __contains__(self, item):
  try:
   self.__getitem__(self, item)
   return True
  except KeyError:
   pass
  return False
 
 def __getitem__(self, item, _recursing=False):
  if self.__cache:
   if isinstance(item, (int, long)):
    return self.__cache["as_list"][item]
   else:
    match = self.__cache["by_bundle_id"].get(item, None)
    if match:
     return match
    match = self.__cache["by_uuid"].get(item, None)
    if match:
     return match
    if not _recursing:
     self.find_all()
     return self.__getitem__(item, _recursing=True)
  raise KeyError(repr(item))
 
 def __iter__(self):
  return self.__list().__iter__()
 
 def __len__(self):
  if self:
   return self.__list().__len__()
  return 0
 
 def __nonzero__(self):
  return bool(self.__cache)

 def get(self, key, default=None):
  try:
   return self[key]
  except KeyError:
   return default
 
 def find(self, query=None, mode=None, path=None, bundle_id=None, uuid=None):
  """Finds an App (or subclass) instance for the given path, bundle ID, or UUID.

This method will use a cache to service the query, creating or re-creating
the cache if necessary.  If the app cannot be found, even after (re-)creating
the cache, the method will return None.

mode can be one of "path", "bundle_id", or "uuid" and takes the place of the
corresponding keyword arguments if set.  Extra arguments are passed to the
class's constuctor if the cache hasn't been created.

(Note:  searching by path is a lie.  This method will check to see if the
path is a valid container or legacy directory, and if so, make a Container
instance for it and see if that has a bundle ID, and then it will look up
that bundle ID if so.)

"""
  if len([i for i in (path, bundle_id, uuid, mode) if i]) is not 1:
   raise ValueError("Please specify only one of path, bundle_id, uuid, or mode.")
  if mode not in ("path", "bundle_id", "uuid", None):
   raise ValueError(repr(mode) + " is not a valid mode.")
  if mode:
   if not query: raise ValueError("Please specify an app to find.")
   if   mode == "path":      path      = query
   elif mode == "bundle_id": bundle_id = query
   elif mode == "uuid":      uuid      = query
  
  made_cache = False
  if not self:
   self.find_all()
   made_cache = True
  
  match = None
  if path:
   try:
    container = Container(path)
    if container.bundle_id:
     match = self.__cache["by_bundle_id"].get(container.bundle_id, None)
     if not match and not made_cache:
      self.find_all()
      match = self.__cache["by_bundle_id"].get(container.bundle_id, None)
   except ContainerError:
    pass
  elif bundle_id:
   match = self.__cache["by_bundle_id"].get(bundle_id, None)
   if not match and not made_cache:
    self.find_all()
    match = self.__cache["by_bundle_id"].get(bundle_id, None)
  elif uuid:
   uuid = uuid.upper()
   match = self.__cache["by_uuid"].get(uuid, None)
   if not match and not made_cache:
    self.find_all()
    match = self.__cache["by_uuid"].get(uuid, None)
  
  return match
 
 def find_all(self):
  """Finds all App Store apps.

Returns self.

This also creates (or re-creates) a memory-backed cache of all apps in
the given root, and this cache is used to service searches for individual
apps.

"""
  index_by_bundle_id = {}
  index_by_uuid      = {}
  apps               = []
  root = self.root
  if root.min_ios >= 8:
   search_roots = (root.bundle_root, root.data_root)
   for type_root in search_roots:
    for container_dir_base in os.listdir(type_root):
     app = None
     try:
      container = Container(os.path.join(type_root, container_dir_base))
      if container.bundle_id:
       class_name = container.class_.name.lower()
       app = index_by_bundle_id.get(container.bundle_id, None)
       if app == None:
        if class_name == "bundle":
         app = self.app_class.__new__(self.app_class, None, None,
                                      *self.app_args, **self.app_kwargs)
	 app.bundle_id = container.bundle_id
         index_by_bundle_id[container.bundle_id] = app
	 apps += [app]
        else:
         continue  # data containers can also be for built-in apps
       if class_name in ("bundle", "data"):
        setattr(app.containers, class_name, container)
        if container.uuid:
         index_by_uuid[container.uuid.upper()] = app
     except ContainerError:
      pass
   for app in apps:
    try:
     if None in (app.containers.bundle, app.containers.data):
      raise AppError()
     app = app.__init__(app.containers.bundle, app.containers.data,
                        *self.app_args, **self.app_kwargs)
    except AppError:
     index_by_bundle_id.pop(app.bundle_id, None)
     bundle_uuid = getattr(app.containers.bundle, "uuid", "").upper()
     data_uuid   = getattr(app.containers.data,   "uuid", "").upper()
     if bundle_uuid:
      index_by_uuid.pop(bundle_uuid, None)
     if data_uuid and data_uuid != bundle_uuid:
      index_by_uuid.pop(data_uuid, None)
     continue
   apps = [app for app in apps if app]
  else:  # root.min_ios < 8
   for container_dir_base in os.listdir(root.legacy_root):
    try:
     container = Container(os.path.join(root.legacy_root, container_dir_base))
     if container.bundle_id:
      try:
       app = self.app_class(container, container,
                            *self.app_args, **self.app_kwargs)
       index_by_bundle_id[container.bundle_id] = app
       if container.uuid:
        index_by_uuid[container.uuid.upper()] = app
       apps += [app]
      except AppError:
       pass
    except ContainerError:
     pass
  
  self.__cache = {
   "by_bundle_id": index_by_bundle_id,
   "by_uuid":      index_by_uuid,
   "as_list":      apps
  }
  
  return self
 
 def sorted(self, key="sort_key"):
  """Returns an iterator that yields each app in the cache sorted according to key.

key is either a string that tells which App attribute should be used as a sort
key, or a callable that is passed an App and returns a sort key.  The default is
"sort_key" (the app's friendly name, converted to lowercase, with diacritical
marks stripped using util.strip_latin_diacritics(), an underscore, and then the
app's bundle ID).

"""
  l = self.__cache["as_list"] if self else []
  if callable(key):
   return sorted(l, key=key)
  else:
   return sorted(l, key=lambda app: getattr(app, key))

#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead programm is a HRI PhD project at the University of Plymouth,
#  a Robotic Animation System including face, eyes, head and other
#  supporting algorithms for vision and basic emotions.
# Copyright (C) 2010 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.

#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Configuration file reading and setting module..

The main function is load() which relies on set_name(project_name) to set the
 name of the project, thus setting the name of the config file to open.

The NAME variable:
------------------
NAME is a string identifying your project.
That string is filtered by isalnum() for portability reasons. Filtered
 characters are replaced with '_'.
From this *filtered* NAME, the configuration file <NAME>.conf is searched.

That file is a python script, declarations are expected to be in that file's
global namespace. In other words is just straightforward declarations.

Configuration file search path order:
-------------------------------------
 1) any path defined by the system variable built from (filtered) NAME value:
   $<NAME>_CONF. eg: MY_PROJECT_CONF='/opt/my_project/my_project.conf'

 2) current user's home directory:
   for POSIX systems: $HOME/.<NAME>.conf ; for Windows there's no leading '.'

 3) global system configuration file:
   for POSIX: /etc/<NAME>.conf ; for Windows C:\\ is used instead


Important Point:  there's only one value for NAME per python process (VM).
================
"""

__version__ = "0.3"
__date__ = ""
__author__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__copyright__ = "Copyright 2011, University of Plymouth"
__license__ = "GPL"
__maintainer__ = "Frédéric Delaunay"
__status__ = "Prototype" # , "Development" or "Production"

import sys
import platform
from os import path, environ

__NAME = None
__LOADED_FILE = None

BASE_PATH=path.normpath(__path__[0]+'/../..')+'/'
CONFIG={}


class LoadingError(StandardError):
    """2 argument (filename and error_message) Exception."""
    def __str__(self):
        return "%s %s" % self.args

class ConfigError(StandardError):
    """2 argument (filename and error_message) Exception."""
    def __str__(self):
        return "%s" % self.args


def set_name(project_name):
    """Sets the project name and returns the filtered version of it.
    >project_name: string identifying the project.
    Return: filtered version of project_name
    """
    global __NAME
    __NAME = filter(lambda x: x.isalnum() and x or '_', project_name)
    return __NAME

def get_name():
    """Return: global (filtered) project name"""
    global __NAME
    assert __NAME, "project name has not been set; use conf.set_name."
    return __NAME

def get_loaded():
    """Return: loaded filename"""
    global __LOADED_FILE
    return __LOADED_FILE

def build_candidates():
    """Returns locations where conf file could be, ie:
    1/ from environmnent variable built from project name (see build_env())
    2/ in user home folder (for SysV and co.: hidden file with leading '.')
    3/ in system's configuration folder (for SysV and co.: /etc , Windows: C:\\)
    Raise: OSError
    """
    locs=[]
    try:
        locs.append(environ[__NAME])
    except (OSError,KeyError):
        pass
    lead = '.' if platform.uname()[0] != 'Windows' else ''
    sysWide_confFolder = '/etc' if platform.uname()[0] != 'Windows' else r'C:\\'
    #XXX the following might raise an OSError
    locs.append(path.join(path.expanduser('~/'),lead+__NAME+'.conf'))
    locs.append(path.join(sysWide_confFolder, __NAME+'.conf'))
    return locs

def load(raise_exception=True, reload_=False, required_entries=(), name=None,
         logger=None):
    """Try to load 1st available configuration file, ignoring Subsequent calls
    unless reload_ is set to True.
    required_names: iterable of strings specifying variable names to be found.
    Returns: [missing_definitions]
    """
    global __NAME, __LOADED_FILE
    if not name:
        get_name()
    else:
        set_name(name)

    ## check for missing mandatory configuration entries.
    def check_missing(required_entries):
        global CONFIG
        return [ i for i in required_entries if
                 i not in CONFIG ]#dir(sys.modules[__name__]) ]

    def load_json(conf_file):
        try:
            import json
            with open(conf_file) as f:
                globals()["CONFIG"]=json.load(f)
        except StandardError as e:
            return e
    def load_python(conf_file):
        try:
            execfile(conf_file, CONFIG)
            return None
        except SyntaxError as err:
            msg = "error line %i." % err.lineno
        except StandardError as e:
            msg = e
        return msg

    ## load file
    def load_from_candidates():
        for conf_file in build_candidates():
            if not path.isfile(conf_file):
                continue
            msg = load_json(conf_file) and load_python(conf_file)
            if msg and raise_exception:
                raise LoadingError(conf_file, msg)
            return conf_file

    if __LOADED_FILE and not reload_:
        return []

    __LOADED_FILE = load_from_candidates()
    if __LOADED_FILE:
        if logger:
            logger.info("Loaded configuration file '%s'", __LOADED_FILE)
    elif raise_exception:
        if logger:
            logger.error("no config file found in any of %s",build_candidates())
        raise LoadingError(None,
                           "** NO CONFIGURATION FILE FOUND FOR PROJECT {0} **"
                           "Aborting!\nYou can define the environment variable"
                           " '{0}' for complete configuration file path "
                           "definition.".format(__NAME) )
    return check_missing(required_entries)

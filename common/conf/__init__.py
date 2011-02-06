#!/usr/bin/python

# Lighthead-bot programm is a HRI PhD project at
#  the University of Plymouth,
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
conf package for the CONCEPT project.
versions >= 2.5
Copyright (C) 2009 frederic DELAUNAY, University of Plymouth (UK).
"""
"""
Configuration file reading and setting module..

Main function is load() which relies on 2 ways to load a configuration file:
- if load() is called without prior call to set_name(), it opens project_def.py (see below).
- if using set_name(project_name) to set the name of the project, you can then call load().

project_def.py:
---------------
This allows specifying the project's name and required configuration entries.
If you have this file, you must define these variables:
 NAME which defines the project name
 REQUIRED which defines required entries (see below).

The NAME variable:
------------------
NAME is a string identifying your project.
That string is filtered by isalnum() for portability reasons. Filtered
 characters are replaced with '_'.
From this *filtered* NAME, the configuration file <NAME>.conf is searched.
 Indeed, that file is a python script, declarations are expected to be in that
 file's global namespace. In other words is just straightforward declarations.

The REQUIRED variable:
----------------------
REQUIRED is an iterable (eg. array or tuple) of strings, defining the entries to
 be found in your project configuration file. eg: REQUIRED = ('address', 'port')
Indeed, you can define REQUIRED as an empty iterable. eg: REQUIRED=(,)

Alternative to project_def.py:
------------------------------
If you don't want to set configuration requirements, you can also define NAME by
 directly calling this module's set_name(). 
 eg: import conf; conf.set_name('foo'); conf.load()

Configuration file search path order:
-------------------------------------
 1) any path defined by the system variable built from (filtered) NAME value:
   $<NAME>_CONF 
   eg: in project_def.py:      NAME='my_project'
       in your environment:    MY_PROJECT_CONF='/opt/my_project/my_project.conf'

 2) current user's home directory:
   for POSIX systems: $HOME/.<NAME>.conf

 3) globlal system configuration file:
   for POSIX: /etc/<NAME>.conf


Conclusions:
============
* there's only 1 NAME per python process (VM).
* if you have no project_def.py and no requirements, use set_name()
"""

import os, sys

NAME = None
REQUIRED = None
__LOADED_FILE = None

ROOT_PATH=os.path.normpath(__path__[0]+'/../..')+'/'

class LoadException(Exception):
    """Exception with 2 elements: filename and error_message. Use like:
    import conf
    try:
      load()
    except conf.LoadException, e:
      print 'file {0[0]} : {0[1]}'.format(e)"""
    pass

def set_name(project_name):
    """Sets the project_name and returns the filtered version of it."""
    global NAME
    NAME = filter(lambda x: x.isalnum() and x or '_', project_name)
    return NAME

def get_name():
    """Tries to fetch NAME and (optional) REQUIRED from project_def.py"""
    global NAME
    if NAME:
        return NAME
    try:
        from project_def import NAME, REQUIRED
    except ImportError, e:
        import sys
        raise LoadException('project_def.py',
                            'The project name has not been set and I cannot '
                            'import the project definition: project_def.py '
                            'in PYTHONPATH: %s (%s)' % (sys.path,e) )

def check_missing():
    """check for missing mandatory configuration entries.
    Returns: [missing_definitions]
    """
    global NAME, REQUIRED
    if not NAME:
        get_name()
    if not REQUIRED:
        return []
    return [ i for i in REQUIRED if i not in dir(sys.modules[__name__]) ]

def build_candidates():
    """Creates locations where conf file could be.
    Checks for a environment variable, name being built from build_env()
    """
    global NAME
    if not NAME:
        get_name()

    locs=[]
    try:
        locs.append(os.environ[NAME])
    except (OSError,KeyError):
        pass
    try:
        locs.append( os.path.join(os.path.expanduser('~/'),'.'+NAME+'.conf') )
    except OSError, err:
        raise LoadException(None, 'Cheesy OS error: %s' % err)
    else:
        locs.append(os.path.join('/etc', NAME+'.conf'))
    return locs

def load(raise_exception=True, reload=False):
    """Try to load 1st available configuration file, ignoring Subsequent calls
    unless reload is set to True.
    required_names: iterable of strings specifying variable names to be found.

    Returns: see check_missing()
    """
    global NAME, __LOADED_FILE
    if not NAME:
        get_name()

    def load_from_candidates():
        global __LOADED_FILE
        for conf_file in build_candidates():
            if os.path.isfile(conf_file):
                msg = None
                try:
                    execfile(conf_file, globals())
                    __LOADED_FILE = conf_file
                except SyntaxError, err:
                    msg = "error line %i." % err.lineno
                except Exception, e:
                    msg = e
                else:
                    break
                if msg and raise_exception:
                    raise LoadException(conf_file, msg)

    if __LOADED_FILE and not reload:
        return check_missing()
    else:
        load_from_candidates()

    if not __LOADED_FILE and raise_exception:
        raise LoadException(None,
                            "No configuration file found for project {0}. "
                            "Aborting!\nYou can define the environment variable"
                            " '{0}' for complete configuration file path "
                            "definition.".format(NAME) )
    return check_missing()

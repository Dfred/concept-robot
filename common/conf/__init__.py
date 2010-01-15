#
# Copyright 2008 Frederic Delaunay, f dot d at chx-labs dot org
#
#  This file is part of the comm module for the concept project: 
#   http://www.tech.plym.ac.uk/SoCCE/CONCEPT/
#
#  conf module is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  conf module is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
"""
conf package for the CONCEPT project.
versions >= 2.5
Copyright (C) 2009 frederic DELAUNAY, University of Plymouth (UK).
"""
"""
Global configuration system reading module. Reads file 'lightbot.conf'.
This module reads the global configuration file and checks missing definitions.
Configuration file search path order:
 1) current user's home directory (posix systems: $HOME)
 2) globlal system configuration file (posix: /etc/)
 3) any path defined by the system variable $(LIGHTBOT_CONF)

Syntax is the python syntax.
This software package shall come with a default configuration file.
"""

import os, sys


MODULE=sys.modules[__name__]

ENV='LIGHTBOT_CONF'
FILE='lightbot.conf'
REQUIRED=['conn_gaze', 'conn_face']

ERR_UNAVAILABLE="No configuration file was found. Aborting!\
 You can define LIGHTBOT_CONF system variable for complete filepath definition."

file_loaded=False

class ConfLoadException(Exception):
    pass

def get_unix_sockets(print_flag=False):
    """Try to get unix sockets from the loaded configuration.
    Returns: [ declared_unix_sockets ]
    """
    if not file_loaded:
        load()
    entries=[getattr(MODULE,c) for c in dir(MODULE) if c.startswith('conn_')]
    sockets=[port for host, port in entries if type(port) == type("")]
    if print_flag:
        print " ".join(sockets)
    return sockets


def check_missing():
    """check for missing mandatory configuration entries.
    Returns: [missing_definitions]
    """
    return [ i for i in REQUIRED if i not in dir(MODULE) ]


def load(reload=False):
    """Try to load 1st available configuration file, ignoring Subsequent calls
    unless reload is set to True.

    Returns: see check_missing()
    """
    global file_loaded
    if reload:
        raise ConfLoadException("reload of conf not coded yet")
    elif file_loaded:
        return check_missing()

    conf_files=[]
    if sys.platform.startswith('linux'):
        try:
            conf_files.append(os.path.join(os.path.expanduser('~/'), '.'+FILE))
        except OSError, err:
            print err
            exit()
        conf_files.append(os.path.join('/etc', FILE))

        try:
            conf_files.append(os.environ[ENV])
        except (OSError,KeyError):
            pass
    else:
        print "Platform not supported yet"
        exit(-1)

    for conf_file in conf_files:
        if os.path.isfile(conf_file):
            try:
                execfile(conf_file, globals())
                file_loaded = conf_file
            except SyntaxError, err:
                print "error line", err.lineno
            break
    if file_loaded == False:
        raise ConfLoadException(conf_file, ERR_UNAVAILABLE)
    return check_missing()

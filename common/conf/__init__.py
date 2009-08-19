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
conf package for python.
versions >= 2.5
Copyright (C) 2009 frederic DELAUNAY, University of Plymouth (UK).
"""
"""
Global configuration system reading module. Reads file 'lightbot.conf'.
This module reads the global configuration file and checks missing definitions before setting them in this module.
Configuration file search path order:
 1) current user's home directory (posix systems: $HOME)
 2) globlal system configuration file (posix: /etc/)
 3) any path defined by the system variable $(LIGHTBOT_CONF)

Syntax is the python syntax.
This software package shall come with a default configuration file.
"""

import os, sys

FILE='lightbot.conf'
REQUIRED=['vision_addr']

def check_missing():
    present = [ i for i in REQUIRED if i in globals() ] 
    return (present == REQUIRED, [ i for i in REQUIRED if i not in present ] )

conf_files = []

if sys.platform.startswith('linux'):
    try:
        conf_files.append(os.path.join(os.path.expanduser('~/'), '.'+FILE))
    except OSError, err:
        print err
        exit()
    conf_files.append(os.path.join('/etc', FILE))

    try:
        conf_files.append(os.path.join(os.environ['LIGHTBOT_CONF'], FILE))
    except (OSError,KeyError):
        pass

else:
    print "Platform not supported yet"
    exit(-1)

found = False
for conf_file in conf_files:
    if os.path.isfile(conf_file):
        try:
            execfile(conf_file)
        except SyntaxError, err:
            print "error line", err.lineno
        found = True
        break

if not found:
    print FILE,"not found in any of these pathes:",conf_files,". Aborting!"
    exit(-1)

is_complete, missing = check_missing()
    

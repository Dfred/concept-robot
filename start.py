#!/usr/bin/python
# -*- coding: utf-8 -*-

# ARAS is the open source software (OSS) version of the basic component of
# Syntheligence's software suite. This software is provided for academic
# research only. Any other use is not permitted.
# Syntheligence SAS is a robotics and software company established in France.
# For more information, visit http://www.syntheligence.com .

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# Copyright 2013 Syntheligence, fdelaunay@syntheligence.com

# This software was originally named LightHead, the Human-Robot-Interaction part
# of the CONCEPT project, which took place at the University of Plymouth (UK).
# The project originated as the PhD pursued by Frédéric Delaunay, who was under
# the supervision of Prof. Tony Belpaeme.
# This PhD project started in late 2008 and ended in late 2011.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

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


#
# Starter script for Lighty.
#
import os
import sys
import platform

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from utils import EXIT_DEPEND, EXIT_CONFIG
from utils import conf


BGE_PYTHON_VERS=2.7
WINSIZE=800,600
NAME="lighty"
COMMAND=[]
BIN_SUFFIX=""

# # TODO: array so path separator is set later on
PYTHONPATH=(os.getenv("PYTHONPATH") or "")+os.path.pathsep
# #PYTHONPATH=$PYTHONPATH:~/opt/lib/python$BGE_PYTHON_VERS

PROJECT_NAME=NAME
PROJECT_DIR=os.getcwd()
PROJECT_EXTRA_PYTHONPATHS=[os.path.join(PROJECT_DIR,"RAS","backends")]

if __name__ != "__main__":
  print "this script is not supposed to be imported"
  exit(EXIT_DEPEND)

if not os.access("./common", os.R_OK|os.X_OK):
  print "could not find the 'common' directory. Aborting!"
  exit(EXIT_DEPEND)

## parsing options
parser = ArgumentParser(
  description="start-up configuring script for ARAS.",
  epilog="All options can be set in one go, such as: %(prog)s -idw",
  formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-d", action='store_true',
                    help="start in debug mode")
parser.add_argument("-w", nargs='?',
                    help="window mode. Set W as WIDTHxHEIGHT. If not "
                    "specified, default resolution is used")
parser.add_argument("-W", action='store_true',
                    help="use wine to start the application")
parser.add_argument("-b", nargs='?', const='blenderplayer',
                    help="use blenderplayer optionally specifying the version"
                    "to use. This option allows using the resolution argument.")
parser.add_argument("-i", action='store_true',
                    help="use ironhide (package bumblebee) for dual graphic "\
                        "card setups")

args = parser.parse_args()
if args.i:
#XXX fun fact: COMMAND.extend(["optirun"]) => vglrun:303:exec: lighty: not found
#XXX adding an argument makes vglrun work (at least version 2.3.2-20121002).
  COMMAND.extend(["optirun", args.d and "-v" or ""])    #XXX spawns 1new process
if args.W:
  PATH_S_=";z:\\"

## shortcuts
# export alias edit_face="blender $PROJECT_DIR/RAS/face/blender/lightHead.blend"

## test config
from RAS import loadnCheck_configuration
missing = loadnCheck_configuration(NAME)
missing is False and exit(EXIT_DEPEND)
missing is None and exit(EXIT_CONFIG)
print "*** Loaded config file '%s'" % conf.get_loaded()
BACKEND = conf.CONFIG["backends"][0]
print "*** Backend set to", BACKEND

## handle MinGW and Windows suffix
# case `uname -s` in
#     MINGW*)
#         BIN_SUFFIX=".exe"
#         ;;
#     Darwin*)
#     	BIN_SUFFIX=".app/"
#     	COMMAND.insert(0,"open")
#     	;;
#     *)
#       BIN_SUFFIX=""
#       ;;
# esac

## define logic checks
def check_blender(args):
  global COMMAND, BIN_SUFFIX, PROJECT_NAME
  if args.b:
    COMMAND.append(args.b)
    args.w and COMMAND.extend(["-w "]+args.w.split('x',1))  
  elif args.w:
    PROJECT_NAME+="-window"

  executable=os.path.join(PROJECT_NAME+BIN_SUFFIX)
  if sys.platform.startswith("win"):
    executable+=".exe"
  if not os.access(executable, os.X_OK):
    print "ERROR: '%s' is not executable." % executable
    exit(EXIT_DEPEND)
  return executable

def check_backend(args):
  global COMMAND
  COMMAND.insert(0,"/usr/bin/python")
  return "__init__.py"

## edit some variables
# if test -n "$WITH_REDWINE"; then
#     COMMAND.insert("wine")
#     BIN_SUFFIX=".exe"
# fi

## optimize and also remove docstrings
if not args.d:
  os.putenv("PYTHONOPTIMIZE","1")

if BACKEND == "blender":
  COMMAND.append(check_blender(args))
elif BACKEND in ("iCub", "katHD400s_6M"):
  COMMAND.append(check_backend(args))
else:
  print "Unknown backend: '%s', please review config file" % BACKEND
  exit(EXIT_CONFIG)

## build environment paths for python
PYTHONPATH+=";".join(PROJECT_EXTRA_PYTHONPATHS)
os.putenv("PYTHONPATH", PYTHONPATH)

## Now launch
if args.d:
  print "+++ Operating System's version of python is:", filter(
    lambda x: x not in "\r\n", sys.version)
  print "+++ PYTHONPATH=%s" % PYTHONPATH
  print "+++ Running:", COMMAND

os.execvp(COMMAND[0], COMMAND[1:] or [""])

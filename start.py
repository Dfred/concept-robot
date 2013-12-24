#!/usr/bin/python

#
#
#

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


BLENDERPLAYER="blenderplayer.blender2.4"
BGE_PYTHON_VERS=2.7
WINSIZE=800,600
NAME="lighty"
PREFIX=""
BIN_SUFFIX=""
EXECUTABLE=""

# # TODO: array so path separator is set later on
PYTHONPATH=os.getenv("PYTHONPATH")
# #PYTHONPATH=$PYTHONPATH:~/opt/lib/python$BGE_PYTHON_VERS

PROJECT_NAME=NAME
# PROJECT_DIR=`pwd`
# PROJECT_EXTRA_PATHS="$PROJECT_DIR/RAS/backends"

if __name__ != "__main__":
    print "this script is not supposed to be imported"
    exit(EXIT_DEPEND)

if not os.access("./common", os.R_OK|os.X_OK):
    print "could not find the 'common' directory. Aborting!"
    exit(EXIT_DEPEND)

## parsing options
parser = ArgumentParser(description="start-up configuring script for ARAS.",
    epilog="All options can be set in one go, such as: %(prog)s -idw",
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-w", action='store_true',
    help="window mode")
parser.add_argument("-b", nargs=2, default=WINSIZE,
    help="use blenderplayer and set resolution")
parser.add_argument("-d", action='store_true',
    help="start in debug mode")
parser.add_argument("-i", action='store_true',
    help="use ironhide (package bumblebee) for dual graphic card setups")
parser.add_argument("-W", action='store_true',
    help="use wine to start the application")

args = parser.parse_args()
if args.i:
    PREFIX="optirun "+PREFIX
if args.W:
    PATH_S_=";z:\\"

## shortcuts
# export alias edit_face="blender $PROJECT_DIR/RAS/face/blender/lightHead.blend"

from RAS import REQUIRED_CONF_ENTRIES

## test config
conf.set_name(NAME)
try:
  missing = conf.load(required_entries=REQUIRED_CONF_ENTRIES)
  loaded = conf.get_loaded()
except conf.LoadingError as e:
  print "WARNING: unable to find any of these files: ", conf.build_candidates()
  exit(EXIT_DEPEND)

## test configuration
print "Checking conf... ",
if missing:
  print "Failed"
  print "In config file '%s', missing required entries:" % loaded, missing
  exit(EXIT_CONFIG)
else:
  BACKEND = conf.ROBOT["main_backend"]
  print "OK (loaded %s)" % loaded
  print "*** Configuration set backend to %s ***" % BACKEND

## handle MinGW and Windows suffix
# case `uname -s` in
#     MINGW*)
#         BIN_SUFFIX=".exe"
#         ;;
#     Darwin*)
#     	BIN_SUFFIX=".app/"
#     	PREFIX="open $PREFIX "
#     	;;
#     *)
#       BIN_SUFFIX=""
#       ;;
# esac

## define logic checks
def check_blender(args):
  global PREFIX, BIN_SUFFIX, PROJECT_NAME
  if args.b:
    PREFIX+=BLENDERPLAYER
    if args.w:
      PREFIX+="-w %s %s " % args.w
  elif args.w:
    PROJECT_NAME+="-window"

  executable="./%s%s" % (PROJECT_NAME, BIN_SUFFIX)
  if not os.access(executable, os.X_OK):
    print "'%s' is not executable." % executable
    exit(EXIT_DEPEND)
  return executable

def check_backend(args):
  global PREFIX, PYTHON
  PREFIX="%s " % PYTHON
  return "__init__.py"

## edit some variables
# if test -n "$WITH_REDWINE"; then
#     PREFIX="wine $PREFIX "
#     BIN_SUFFIX=".exe"
# fi

## optimize and also remove docstrings
if not args.d:
    os.putenv("PYTHONOPTIMIZE","1")

if BACKEND == "blender":
    EXECUTABLE=check_blender(args)
elif BACKEND in ("iCub", "katHD400s_6M"):
    EXECUTABLE=check_backend(args)
else:
    print "Unknown backend: '%s', please review config file" % BACKEND
    exit(EXIT_CONFIG)

## Now launch
COMMAND="PYTHONPATH=%s %s %s" % (PYTHONPATH, PREFIX, EXECUTABLE)
if args.d:
  print "*** Operating System's version of python is:", sys.version
  print "*** launching %s ***" % BACKEND
  print "running: '%s'" % COMMAND
#if [ $# -ge 1 ]; then echo "using options: $@"; else echo ""; fi

exit(os.system(COMMAND))

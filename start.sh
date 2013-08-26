#!/bin/sh

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


#
# Starter script for LightHead-bot.
#

export PYTHONOPTIMIZE=1	# optimize and also remove docstrings
BGE_PYTHON_VERS=2.7
PROJECT_NAME=lightHead
PROJECT_DIR=`pwd`
# TODO: array so path separator is set later on
PROJECT_EXTRA_PATHS="/usr/lib/python$BGE_PYTHON_VERS/dist-packages:./RAS/face/:./extern"
BLEND_DIR=~/opt/blender-2.49b-linux-glibc236-py26-x86_64

if test -z "$PYTHON"; then
    PYTHON=python$BGE_PYTHON_VERS	#/usr/bin/python3
    echo "unset \$PYTHON, now set to: $PYTHON"
fi
if test -z "$PYTHONHOME"; then
    PYTHONHOME=/usr/lib/python$BGE_PYTHON_VERS
    echo "unset \$PYTHONHOME, now set to: $PYTHONHOME"
fi

if ! $PYTHON -c 'print'; then
    echo "python has an issue. Did you set \$PYTHON ?"
    exit 1
fi

if ! test -d "./common"; then
	echo "could not find directory $CONCEPT_DIR/common . Aborting ..."
	exit 1
fi

# parsing options
OPTIONS="widW"
OPT="-"
PREFIX="$BLEND_DIR/blenderplayer "
while [ "$OPT" != "?" ]
do getopts $OPTIONS OPT
case "$OPT" in
    "w")
        WINDOW_MODE=1
	if test -z "$2" || test -z "$3"; then
	    echo "windowing (-w) option requires width and height arguments"
	    exit 1
	fi
	PREFIX="$PREFIX -w $2 $3 "
	;;
    "i")
    	PREFIX="optirun $PREFIX "
	;;
    "d")
	PREFIX="$PREFIX-d "
	;;
    "W")
        WITH_REDWINE=1
        PATH_S_=";z:\\"
	;;
esac
done

# shortcuts
alias edit_face="blender $PROJECT_DIR/RAS/face/blender/lightHead.blend"


#
# set environment
#
. ./common/source_me_to_set_env.sh

# debugging info
echo "Python version:" $(get_version)
#echo "\$PYTHONPATH=$PYTHONPATH"

# handle MinGW and Windows suffix
case `uname -s` in
    MINGW*)
        BIN_SUFFIX=".exe"
        ;;
    Darwin*)
    	BIN_SUFFIX=".app/"
    	PREFIX="open $PREFIX "
    	;;
    *)
        BIN_SUFFIX=""
        ;;
esac

# edit some variables
if test -n "$WINDOW_MODE"; then
    PROJECT_NAME=$PROJECT_NAME-window
fi
if test -n "$WITH_REDWINE"; then
    PREFIX="wine $PREFIX "
    BIN_SUFFIX=".exe"
fi

# checking environment variable
if test -z "$CONF_FILE"; then
    echo "Missing configuration file."
    exit 3
fi

if ! test -x ./$PROJECT_NAME$BIN_SUFFIX; then
    echo "Could not find executable file '$PROJECT_NAME$BIN_SUFFIX' in this directory."
    exit 2
fi

# Now launch
echo "--- launching face --- "
echo "running: '$PREFIX$PROJECT_NAME$BIN_SUFFIX' " #$@"
#if [ $# -ge 1 ]; then echo "using options: $@"; else echo ""; fi

$PREFIX$PROJECT_NAME$BIN_SUFFIX

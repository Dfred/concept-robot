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

BGE_PYTHON_VERS=2.6
FACE_BIN="lightHead"
CONF_BASENAME="lightHead.conf"

. common/source_me.sh

check_exiting "test -x ./$FACE_BIN" "Could not find executable file '$FACE_BIN' in this directory."
check_exiting "python -c 'print'"  "python not found. Did you set your PATH ?"

# Platform dependent paths (handles the famous nagger thanks to minGW)
case `uname -s` in
	MINGW*)
	MODULES_PATH='common;HRI;HRI/face'
	PYTHONPATH="$MODULES_PATH"
	;;
	*)
	MODULES_PATH='common:HRI:HRI/face'
        # The following depends on the BGE python version (necessary for blender 2.4x)
        BGE_PYTHON_PATH="/usr/lib/python$BGE_PYTHON_VERS/:/usr/lib/python$BGE_PYTHON_VERS/lib-dynload"
        PYTHONPATH="$PYTHONPATH:$BGE_PYTHON_PATH:$MODULES_PATH"
;;
esac
export PYTHONPATH

CONF_FILE=$(get_python_conf $CONF_BASENAME)
# if command failed
if test $? -eq 1; then
    echo $CONF_FILE
    FILES=$(get_python_conf_candidates $CONF_BASENAME)
    echo '\t\t     files searched for: ' $FILES
    exit 1
fi


MISSING=$(check_python_conf $CONF_BASENAME)
if ! test -z "$MISSING"; then
    echo "missing entries in conf: $MISSING"
    exit 1
fi

ADDR_PORT=`grep "$FACE_BIN"_server $CONF_FILE | cut -d '=' -f2`
echo "--- Using $CONF_FILE -> Listening on $ADDR_PORT "

# remove old unix sockets if present
SOCKETS=`python -c 'import conf; conf.NAME="'$CONF_BASENAME'"; conf.get_unix_sockets(1)'`
if test $? -ne 0; then
	echo "ERROR: Failure to get socket list !"
	exit 1
fi
if test -n "$SOCKETS" ; then
	echo "deleting old sockets: "
	for s in $SOCKETS; do
	  if test -S "$s"; then echo "  "`rm -v "$s"` ; fi
	done
fi

# Now launch
echo -n "--- launching face "
if [ $# -ge 1 ]; then echo "using options: $@"; else echo ""; fi
./$FACE_BIN $@ "$CONF_BASENAME"

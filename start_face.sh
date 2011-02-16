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
BGE_PYTHON_VERS=2.6
PROJECT_NAME=lightHead

if ! python -c 'print'; then
    echo "python not found. Did you set your PATH ?"
    exit 1
fi

. ./source_me_to_set_env.sh

# handle MinGW and Windows suffix
case `uname -s` in
    MINGW*)
        BIN_SUFFIX=".exe"
        ;;
    *)
        BIN_SUFFIX=""
        ;;
esac

if ! test -x ./$PROJECT_NAME$BIN_SUFFIX; then
    echo "Could not find executable file '$PROJECT_NAME' in this directory."
    exit 1
fi

if test -z "$CONF_FILE"; then
    exit 1
fi

# Now launch
getopts "w" OPTS
if [ "$OPTS" = "w" ]; then
    shift;
fi

echo -n "--- launching face ---"
if [ $# -ge 1 ]; then echo "using options: $@"; else echo "";
fi

if [ "$OPTS" = "w" ]; then
    ./$PROJECT_NAME-window$BIN_SUFFIX $@ "$PROJECT_NAME"
else
    ./$PROJECT_NAME$BIN_SUFFIX $@ "$PROJECT_NAME"
fi

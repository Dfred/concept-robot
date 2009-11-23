#!/bin/bash

FACE_BIN="lightbot_face"

if ! test -x ./$FACE_BIN; then
    echo
    echo "This script expects to find in this directory the executable file '$FACE_BIN'."
    echo "Open the appropriate .blend file with blender (version >= 2.49) and use its menu (File->Save Game as Runtime...) to generate the file for your system."
    echo
else

    BGE_SCRIPT_PATH=:common/:HRI

# The following depends on internal BGE python version

    BGE_PYTHON_VERS=2.5
    BGE_PYTHON_PATH=/usr/lib/python$BGE_PYTHON_VERS/:/usr/lib/python$BGE_PYTHON_VERS/lib-dynload

# set standard conf if not set yet
    if test -z "$LIGHTBOT_CONF" ; then
        export LIGHTBOT_CONF=./common/lightbot.conf
    fi

# remove old unix sockets if present
    SOCKETS=`PYTHONPATH=$BGE_SCRIPT_PATH python -c 'import conf; conf.get_unix_sockets(1)'`
    if test -n "$SOCKETS" ; then
        echo "deleting old sockets"
        for s in $SOCKETS; do
            if test -S "$s"; then rm -v "$s"; fi
        done
    fi

# Now launch
    echo -n "launching face "
    if [ $# -ge 1 ]; then echo "using options: $@"; else echo ""; fi
    PYTHONPATH="$PYTHONPATH:$BGE_PYTHON_PATH:$BGE_SCRIPT_PATH" ./$FACE_BIN $@
fi

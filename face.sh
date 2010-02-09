#!/bin/bash

FACE_BIN="lightbot_face"

if ! test -x ./$FACE_BIN; then
    echo
    echo "Could not find executable file '$FACE_BIN' in this directory."
    echo
else

    BGE_SCRIPT_PATH=:common/:HRI:HRI/face

# The following depends on internal BGE python version

    BGE_PYTHON_VERS=2.5
    BGE_PYTHON_PATH=/usr/lib/python$BGE_PYTHON_VERS/:/usr/lib/python$BGE_PYTHON_VERS/lib-dynload

# set standard conf if not set yet
    if test -z "$LIGHTBOT_CONF" ; then
        export LIGHTBOT_CONF=./common/lightbot.conf
    fi

# remove old unix sockets if present
    SOCKETS=`PYTHONPATH=$BGE_SCRIPT_PATH python -c 'import conf; conf.get_unix_sockets(1)'`
    if test $? -ne 0; then
	echo "ERROR: Failure to get socket list !"
	exit -1
    fi
    if test -n "$SOCKETS" ; then
        echo "deleting old sockets: "
        for s in $SOCKETS; do
            if test -S "$s"; then echo "  "`rm -v "$s"` ; fi
        done
    fi

# Now launch
    echo -n "launching face "
    if [ $# -ge 1 ]; then echo "using options: $@"; else echo ""; fi
    PYTHONPATH="$PYTHONPATH:$BGE_PYTHON_PATH:$BGE_SCRIPT_PATH" ./$FACE_BIN $@
fi

#!/bin/bash

BASE_DIR="$HOME/concept/concept-robot-remote"

TARGET_BIN="$HOME/Blender/blender"

BGE_SCRIPT_PATH="$BASE_DIR/common/:$BASE_DIR/HRI/:$BASE_DIR/HRI/face"

# The following depends on internal BGE python version

    BGE_PYTHON_VERS=2.5
    BGE_PYTHON_PATH=/usr/lib/python$BGE_PYTHON_VERS/:/usr/lib/python$BGE_PYTHON_VERS/lib-dynload

# set standard conf if not set yet
    if test -z "$LIGHTBOT_CONF" ; then
        export LIGHTBOT_CONF=$BASE_DIR/common/lightbot.conf
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

    if [ $1 != "clean" ]; then
	# Now launch
	echo "launching" `basename $TARGET_BIN`
	PYTHONPATH="$PYTHONPATH:$BGE_SCRIPT_PATH" $TARGET_BIN $@
    fi

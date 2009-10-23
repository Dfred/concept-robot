#!/bin/sh

FACE_BIN="lightbot_face"

if ! test -x ./$FACE_BIN; then
    echo
    echo "This script expects to find in this directory the executable file '$FACE_BIN'."
    echo "Open the appropriate .blend file with blender (version >= 2.49) and use its menu (File->Save Game as Runtime...) to generate the file for your system."
    echo
else

    BGE_SCRIPT_PATH=:common:HRI/face

# The following depends on internal BGE python version

    BGE_PYTHON_VERS=2.5
    BGE_PYTHON_PATH=/usr/lib/python$BGE_PYTHON_VERS/:/usr/lib/python$BGE_PYTHON_VERS/lib-dynload

# Now launch
    echo -n "launching face "
    if [ $# -ge 1 ]; then echo "using options: $@"; else echo ""; fi
    PYTHONPATH=$PYTHONPATH:$BGE_PYTHON_PATH:$BGE_SCRIPT_PATH ./$FACE_BIN $@
fi
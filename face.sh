#!/bin/sh

echo "This scripts expects to find in this directory the standalone blender file as 'lightbot_face'. Use blender (Save game as runtime...) to generate the file for your system."

BGE_SCRIPT_PATH=:common:HRI/blender

# The following depends on internal BGE python version

BGE_PYTHON_VERS=2.5
BGE_PYTHON_PATH=/usr/lib/python$BGE_PYTHON_VERS/:/usr/lib/python$BGE_PYTHON_VERS/lib-dynload

# Now launch

PYTHONPATH=$PYTHONPATH:$BGE_PYTHON_PATH:$BGE_SCRIPT_PATH ./lightbot_face

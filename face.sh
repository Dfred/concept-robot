#!/bin/sh
#
# Starter script for LightHead.
#

BGE_PYTHON_VERS=2.6
FACE_BIN="lightbot_face"

check()
{
  if ! $1; then
	echo
	echo $2
	exit -1
  fi
}

check "test -x ./$FACE_BIN" "Could not find executable file '$FACE_BIN' in this directory."
check "python -c 'print'"  "python not found. Did you set your PATH ?"

# Platform dependent paths (handles the famous nagger)
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

# set standard conf if not set yet
if test -z "$LIGHTBOT_CONF" ; then
	export LIGHTBOT_CONF=./common/lightbot.conf
fi

# remove old unix sockets if present
python -c 'import conf; conf.load(); print "using file", conf.file_loaded'
SOCKETS=`python -c 'import conf; conf.get_unix_sockets(1)'`
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
echo -n "--- launching face "
if [ $# -ge 1 ]; then echo "using options: $@"; else echo ""; fi
./$FACE_BIN $@

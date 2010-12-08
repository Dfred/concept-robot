#
# This script is meant to be sourced (aka the . command).
# This script:
#  * checks folders
#  * checks which configuration file is loadable
#
#  * relies on PROJECT_NAME environment variable
#
#  * sets the PYTHONPATH environment variable
#  * sets the CONF_FILE environment variable
#  * sets the edit_face alias
#

if test -z "$CONCEPT_DIR"; then
    echo '$CONCEPT_DIR' not set, assuming '$PWD' "($PWD)"
    CONCEPT_DIR=$PWD
fi

# test known errors 1st
if ! test -d "$CONCEPT_DIR/common"; then
	echo "could not find directory $CONCEPT_DIR/common . Aborting ..."
elif test -z "$PROJECT_NAME"; then
    echo '$PROJECT_NAME' not set, cannot continue.
else
    # Platform dependent paths (handles the famous nagger thanks to minGW)
    case `uname -s` in
	MINGW*)
	    MODULES_PATH="$CONCEPT_DIR/common;$CONCEPT_DIR/HRI;$CONCEPT_DIR/HRI/face"
	    PYTHONPATH="$MODULES_PATH"
	    ;;
	*)
	    MODULES_PATH="$CONCEPT_DIR/common:$CONCEPT_DIR/HRI:$CONCEPT_DIR/HRI/face"
            # The following depends on the BGE python version (necessary for blender 2.4x)
            BGE_PYTHON_PATH="/usr/lib/python$BGE_PYTHON_VERS/:/usr/lib/python$BGE_PYTHON_VERS/lib-dynload"
            PYTHONPATH="$PYTHONPATH:$BGE_PYTHON_PATH:$MODULES_PATH"
	    ;;
    esac
    export PYTHONPATH

    . $CONCEPT_DIR/common/source_me.sh

    CONF_FILE=$(get_python_conf $PROJECT_NAME)
    if test $? != 0 ; then
	echo "$CONF_FILE"
	unset CONF_FILE
    else
	if ! test -z "$CONF_FILE"; then
	    echo "found configuration file: " $CONF_FILE
	    export CONF_FILE
	else
	    echo -n "the conf module could not find any of these files: "
	    echo `get_python_conf_candidates $PROJECT_NAME`
	fi

	MISSING= check_python_conf $PROJECT_NAME
	if ! test -z "$MISSING"; then
	    echo "missing entries in conf: $MISSING"
	fi

	if ! test -r "$CONF_FILE"; then
	    echo "WARNING: $CONF_FILE could not be found or is not readable."
	    echo "Edit project_def.py or $PROJECT_NAME environment variable."
	fi
    fi
    alias edit_face="blender $CONCEPT_DIR/HRI/face/blender/lightHead.blend"
fi


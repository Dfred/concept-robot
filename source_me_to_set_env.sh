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

# override PROJECT_NAME if given an argument
if test $0 != './start_face.sh' && test -n "$1"; then
    PROJECT_NAME=$1
fi

# test known errors 1st
if ! test -d "$CONCEPT_DIR/common"; then
	echo "could not find directory $CONCEPT_DIR/common . Aborting ..."
elif test -z "$PROJECT_NAME"; then
	echo "missing argument or "'$PROJECT_NAME'" not set: cannot continue."
else
    echo "Setting environment for project: $PROJECT_NAME"

    DIST_PACKS_PATH=/usr/lib/python2.6/dist-packages

    # Platform dependent paths (handles the famous nagger thanks to minGW)
    case `uname -s` in
	MINGW*)
	    MODULES_PATH="$CONCEPT_DIR;$CONCEPT_DIR/common;$CONCEPT_DIR/HRI:$CONCEPT_DIR/ext/"
	    PYTHONPATH="$MODULES_PATH"
	    ;;
	*)
	    MODULES_PATH="$CONCEPT_DIR:$CONCEPT_DIR/common:$CONCEPT_DIR/HRI:$CONCEPT_DIR/ext/"
            PYTHONPATH="$PYTHONPATH:$DIST_PACKS_PATH:$MODULES_PATH"
	    ;;
    esac
    export PYTHONPATH

    # Load helper functions (calling python)
    . $CONCEPT_DIR/common/source_me.sh

    CONF_FILE=$(get_python_conf $PROJECT_NAME)
    if test $? != 0 ; then
	echo "$CONF_FILE"
	unset CONF_FILE
    else
	if test -n "$CONF_FILE"; then
	    echo "found configuration file: " $CONF_FILE
	    export CONF_FILE
	else
	    echo -n "WARNING: unable to find any of these files: "
	    echo `get_python_conf_candidates $PROJECT_NAME`
	    echo "Edit project_def.py or $PROJECT_NAME environment variable."
	fi

	MISSING= check_python_conf $PROJECT_NAME
	if test -n "$MISSING"; then
	    echo "missing required entries in conf: $MISSING"
	fi
    fi
    alias edit_face="blender $CONCEPT_DIR/HRI/face/blender/lightHead.blend"
fi

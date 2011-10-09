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
    echo '$CONCEPT_DIR' not set, assuming $PWD
    CONCEPT_DIR=$PWD
fi

# set PROJECT_NAME if given an argument
if test -z "$PROJECT_NAME" && test "$0" != './start_face.sh' && test -n "$1";
 then
    PROJECT_NAME=$1
    echo "set PROJECT_NAME to $1"
fi

# test common errors 1st
if test -z "$PROJECT_NAME"; then
	echo "missing argument or "'$PROJECT_NAME'" not set: cannot continue."
else
    echo "Setting environment for project: $PROJECT_NAME"
    # Load helper functions (calling python)
    . $CONCEPT_DIR/common/source_me_python_conf_fcts.sh
    # reset CONCEPT_DIR (minGW paths are screwing python's os.path)
    CONCEPT_DIR=$(get_CWD)

    # Platform dependent paths (handles the famous nagger thanks to minGW)
    case `uname -s` in
	MINGW*)
            PATH_S_=';'
#            DIST_PACKS_P='c:\Python26\lib\site-packages'
            ;;
	*)
            PATH_S_=':'
#            DIST_PACKS_P='/usr/lib/python2.6/dist-packages'
	    ;;
    esac
    EXTRA="$CONCEPT_DIR/RAS/face/$PATH_S_$CONCEPT_DIR/extern"
    MODULES_PATH="$CONCEPT_DIR/$PATH_S_$EXTRA"
    export PYTHONPATH="$PYTHONPATH$PATH_S_$DIST_PACKS_P$PATH_S_$MODULES_PATH"

    CONF_FILE=$(get_python_conf $PROJECT_NAME)
    if test "$?" != 0 ; then
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

        echo -n "Checking conf... "
	MISSING=$(check_python_conf $PROJECT_NAME)
	if test -n "$MISSING"; then
	    echo "missing required entries in conf: $MISSING"
	else
	    echo "OK"
	fi
    fi
    alias edit_face="blender $CONCEPT_DIR/RAS/face/blender/lightHead.blend"
fi

#
# This script is meant to be sourced (aka the . command).
# This script:
#  * checks folders
#  * checks which configuration file is loadable
#
#  * sets the PYTHONPATH environment variable
#  * sets the LIGHTHEAD_CONF environment variable
#  * sets the edit_face alias
#

if test -z "$CONCEPT_DIR"; then
    echo '$CONCEPT_DIR' not set, assuming '$PWD' "($PWD)"
    CONCEPT_DIR=$PWD
fi
if ! test -d "$CONCEPT_DIR/common"; then
	echo "could not find directory $CONCEPT_DIR/common . Aborting ..."
else
    PYTHONPATH=$PYTHONPATH:$CONCEPT_DIR/common/:$CONCEPT_DIR/HRI/
    export PYTHONPATH

    source $CONCEPT_DIR/common/source_me.sh
    CONF_BASENAME='lightHead.conf'

    LIGHTHEAD_CONF=$(get_python_conf $CONF_BASENAME)
    if test $? != 0 ; then 
	echo "$LIGHTHEAD_CONF"
    else
	if ! test -z "$LIGHTHEAD_CONF"; then
	    echo "found configuration file: " $LIGHTHEAD_CONF
	    export LIGHTHEAD_CONF
	else
	    echo -n "the conf module could not find any of these files: "
	    echo `get_python_conf_candidates $CONF_BASENAME`
	fi

	MISSING= check_python_conf $CONF_BASENAME
	if ! test -z "$MISSING"; then
	    echo "missing entries in conf: $MISSING"
	fi

	if test -z "$LIGHTHEAD_CONF"; then
	    export LIGHTHEAD_CONF=$CONCEPT_DIR/common/lightHead.conf
	fi

	if ! test -r "$LIGHTHEAD_CONF"; then
	    echo "WARNING: $CONF_BASENAME could not be found or is not readable. Check your LIGHTHEAD_CONF variable."
	fi
    fi
    alias edit_face="blender $CONCEPT_DIR/HRI/face/blender/lighthead.blend"
fi

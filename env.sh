#
# This script sets various environment variables required or optional to the system.
#

if test -z "$CONCEPT_DIR"; then
    echo '$CONCEPT_DIR' not set, assuming '$PWD' "($PWD)"
    CONCEPT_DIR=$PWD
fi

ETC_CONF=/etc/lightHead.conf
PYTHONPATH=$PYTHONPATH:$CONCEPT_DIR/common/:$CONCEPT_DIR/HRI/

if test -z "$LIGHTHEAD_CONF"; then
	export LIGHTHEAD_CONF=$CONCEPT_DIR/lightHead.conf
fi

if ! test -r $ETC_CONF && ! test -r "$LIGHTHEAD_CONF"; then
	echo "WARNING: no config file found: $ETC_CONF nor $LIGHTHEAD_CONF. Check your LIGHTHEAD_CONF variable."
fi

export PYTHONPATH

alias edit_face="blender $CONCEPT_DIR/HRI/face/blender/lighthead.blend"

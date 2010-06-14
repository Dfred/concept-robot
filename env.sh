ETC_CONF=/etc/lightHead.conf

if test -z "$CONCEPT_DIR"; then
    echo '$CONCEPT_DIR' not set, assuming '$PWD' "($PWD)"
    CONCEPT_DIR=$PWD
fi

export PYTHONPATH=$PYTHONPATH:$CONCEPT_DIR/common/:$CONCEPT_DIR/HRI/:$CONCEPT_DIR/HRI/face/

if test -z "$LIGHTHEAD_CONF"; then
	export LIGHTHEAD_CONF=$CONCEPT_DIR/lightHead.conf
fi

if ! test -r $ETC_CONF && ! test -r "$LIGHTHEAD_CONF"; then
	echo "WARNING: no config file found: $ETC_CONF nor $LIGHTHEAD_CONF. Check your LIGHTHEAD_CONF variable."
fi

alias edit_face="blender $CONCEPT_DIR/HRI/face/blender/lighthead.blend"

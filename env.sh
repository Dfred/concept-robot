if test -z "$CONCEPT_DIR"; then
    echo '$CONCEPT_DIR' not set, assuming '$PWD' "($PWD)"
    CONCEPT_DIR=$PWD
fi
export PYTHONPATH=$PYTHONPATH:$CONCEPT_DIR/common/:$CONCEPT_DIR/HRI/:$CONCEPT_DIR/HRI/face/
export LIGHTBOT_CONF=$CONCEPT_DIR/lightbot.conf

alias edit_face="blender $CONCEPT_DIR/HRI/face/blender/lighthead.blend"

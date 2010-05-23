if test -z "$CONCEPT_DIR"; then
    echo '$CONCEPT_DIR' not set, assuming '$PWD' "($PWD)"
    CONCEPT_DIR=$PWD
fi
export PYTHONPATH=$PYTHONPATH:$CONCEPT_DIR/common/
export LIGHTBOT_CONF=$CONCEPT_DIR/lightbot.conf

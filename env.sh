if test -z "$CONCEPT_DIR"; then
    echo '$CONCEPT_DIR' not set, assuming '$HOME' "($HOME)"
    CONCEPT_DIR=$HOME
fi
export PYTHONPATH=$CONCEPT_DIR/common/
export LIGHTBOT_CONF=$CONCEPT_DIR/lightbot.conf

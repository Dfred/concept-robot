if ! test -f `basename ./$0`; then
    echo "you should start this script from the directory where you found it"
elif test -z "$1"; then
    echo "usage: $0 player_file"
else
    EXP_DIR=`pwd`
    cd ../..
    source ./common/source_me_to_set_env.sh lightHead

    python $EXP_DIR/player_monologue.py -n "$EXP_DIR$@"
fi


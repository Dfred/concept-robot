if test -f ./start_blink_exp.sh; then
    cd ../..
else
    echo 'you should start this script from the directory where you found it'
fi
EXP_DIR=./experiments/blink-influence/
source ./common/source_me_to_set_env.sh lightHead

python $EXP_DIR/player_monologue.py -n "$EXP_DIR$@"

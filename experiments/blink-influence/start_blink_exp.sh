if test -f ./start_blink_exp.sh; then
    cd ../..
else
    echo 'you may start this script from the top directory or where you found it'
fi

source ./common/source_me_to_set_env.sh lightHead

python ./experiments/blink-influence/player_monologue.py $@

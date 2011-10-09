#!/bin/bash
OUR_DIR=`pwd`
cd ../..
export PYTHONPATH=$PYTHONPATH:./extern/pyvision/

declare -a ARGS=("$@")
unset ARGS[0]

case $1 in
	voice)
		julius -quiet -input mic -C $OUR_DIR/interfaces/julian.jconf 2>/dev/null | python $OUR_DIR/interfaces/voice_command.py ${ARGS[@]};;
	*)
		python $OUR_DIR/main.py $@;;
esac

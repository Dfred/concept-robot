#!/bin/bash
export PYTHONPATH=$PYTHONPATH:../common/:../HRI/:../HRI/vision/pyvision_0.9.0/src/:control/:learning/:interfaces/

declare -a ARGS=("$@")
unset ARGS[0]

case $1 in
	voice)
		PYTHONPATH=$PYTHONPATH:`dirname $0`
		julius -quiet -input mic -C julian.jconf 2>/dev/null | python ./interfaces/voice_command.py ${ARGS[@]};;
	*)
		./main.py $@;;
esac

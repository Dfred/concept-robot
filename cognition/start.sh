#!/bin/sh
export PYTHONPATH=../common/:../HRI/:../HRI/vision/pyvision_0.9.0/src/:control/:learning/:

case $1 in
	voice)
		julius -quiet -input mic -C julian.jconf 2>/dev/null | ./control/voice_command.py;;
	*)
		./main.py;;
esac

#!/bin/bash

if [ $# == 0 ]; then
    RES_DIR=./results
else
    RES_DIR=$1
    shift
fi

if ! test -d "$RES_DIR"; then
    echo "$RES_DIR directory not found. Where are the results !?"
    exit -1
fi


for DISP in "dome" "flat" "human" "mask"
do 
    echo "processing results for $DISP" #in file result-$DISP.txt
    for SEQ in $RES_DIR/sequence-$DISP-*
    do
        PAIR=`basename $SEQ | cut -d- -f3`
        if [ $PAIR == '.txt' ]; then PAIR="A-Z"; fi
#        echo -n "$PAIR"
        for RES in $RES_DIR/$DISP-[$PAIR]-*
        do
            ./analyse-results.py $SEQ $RES $@ #>> result-$DISP.txt
        done
    done
    echo ""
done

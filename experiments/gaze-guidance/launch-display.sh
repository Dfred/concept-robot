#!/bin/bash

ARGS=("human" "lightbot" "bubble")   #that's an array

# COMMON PARAMETERS
DELAY=5
TRIES=50
PYTHONPATH=$PYTHONPATH:`pwd`/../../common/
TWD=`pwd`

# HUMAN PARAMETERS
VOICE=voice_us1_mbrola # or empty

# LIGHTBOT PARAMETERS
HOST="localhost"
VIS_SOCK="/tmp/vision"
VISION="$TWD/../../HRI/vision/vision.py"
LIGHTBOT="./face.sh"
COMM_CLIENT="$TWD/../../common/readline_client"
AZIMUTH="-4 + 18"
ALTITUDE="-4 + 18"

# check arguments number
if ! test "$#" -eq 1; then
    echo "exactly 1 argument expected amongst: ${ARGS[@]}"
    exit -1
fi

# prepare programms
case "$1" in
    ${ARGS[0]})
    echo "Are the headphones connected ? Sound volume tuned ?"
    echo "press Enter key to start"
    read ;;

    ${ARGS[1]} | ${ARGS[2]})
    
    if ! test -S "$VIS_SOCK"; then
        echo "starting vision"
        $VISION &
    fi
    cd $TWD/../../ && $LIGHTBOT & cd $TWD
    DELAY=4
    read ;;

    *)
        echo "Sorry this argument is not recognized (PEBKAC)."
        exit -1
        ;;
esac

# main loop part
gazeAt()
{
    echo "##!@#!@#!@#!@#!@#!@!-----------" $1
    x=`echo "$1%10 * $AZIMUTH" | bc`
    y=`echo "$1/10 * $ALTITUDE" | bc`
    echo "focus $x -40 $y" | $COMM_CLIENT --pipe $HOST $VIS_SOCK
    aplay ding.wav &
}

RESFILE=sequence-$1-`date +%j-%H%M%S`.txt
echo "Will write generated numbers to $RESFILE"
i=0
while [ $i -lt $TRIES ]
do i=$(($i+1))
    N=`echo "$RANDOM*99/32767" | bc`
    case $1 in 
        ${ARGS[0]})
        echo "#$i - $N"; echo "($VOICE) (SayText $N)" | festival --pipe ;;
        ${ARGS[1]} | ${ARGS[2]})
        gazeAt $N
        ;;
    esac
    echo $N >> $RESFILE
    sleep $DELAY
done

# cleanup
if [ "$1" == ${ARGS[1]} ] || [ "$1" == ${ARGS[2]} ]; then
    echo "shutdown" | $COMM_CLIENT --pipe $HOST $VIS_SOCK
fi

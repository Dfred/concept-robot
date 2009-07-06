DELAY=5
TRIES=50
RESFILE=sequence-`date +%H%M%S`.txt
VOICE=voice_us1_mbrola # or empty

echo "writting number sequence to $RESFILE"

i=0
while [ $i -lt $TRIES ]
        do i=$(($i+1))
        N=`echo "$RANDOM*99/32767" | bc`
        echo "#$i - $N"; echo "($VOICE) (SayText $N)" | festival --pipe
        echo $N >> $RESFILE
        sleep $DELAY
done

#!/usr/bin/python

import sys

seqs = []
for f in sys.argv[1:]:
    seqs.append([ int(n) for n in file(f) ])

f = file('sequence-'+sys.argv[1][9:13]+'S.txt', 'w')
buff=''
for s in seqs:
    buff+= str(s)+'\n'

f.write(buff)
f.close()

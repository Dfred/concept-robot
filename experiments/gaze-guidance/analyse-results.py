#!/usr/bin/python

import sys

def cmp(real, test):
    x = abs(real%10 - test%10)
    y = abs(real/10 - test/10)
    return x == y and 1.5 *x or x+y


real = [int(n) for n in file(sys.argv[1])]
test = [int(n) for n in file(sys.argv[2])]

diff = 0
for i in xrange(len(real)):
    diff += cmp(real[i], test[i])

print diff
    

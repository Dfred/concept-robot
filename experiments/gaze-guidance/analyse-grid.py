#!/usr/bin/python

import sys

HELP="usage: ./analyse-grid participants_scores ref_sequence1 ref_sequence2 ..\n
participants_scores file shall be the result of the analyse-all.sh with the --grid option 
There should be as many score lines in the 1st file as the number of ref_sequence files."

grid_total = [0]*100
lines = [ eval(grid) for grid in file(sys.argv[1]) if grid[0] == '[' ]
for line in lines:
    for i in xrange(len(line)):         # iterate over the numbers of a line
        if len(sys.argv) == 2:          # count total error
            grid_total[i] += line[i]
        elif sys.argv[2] == 'seq':      # count occurrences of number
            grid_total[line[i]] += 1
print "average grid_total

import Image

img = Image.new('L', (10,10))    # 8-bit pixels, black and white
img.putdata(grid_total, 256/max(grid_total))
img = img.resize((100,100))
img.save(sys.argv[1]+'.bmp')
img.show()

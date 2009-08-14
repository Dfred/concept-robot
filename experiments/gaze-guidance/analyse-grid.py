#!/usr/bin/python

import sys

grid_total = [0]*100

lines = [ eval(grid) for grid in file(sys.argv[1]) if grid[0] == '[' ]

for line in lines:
    for i in xrange(len(line)):         # iterate over the numbers of a line
        if len(sys.argv) == 2:          # count total error
            grid_total[i] += line[i]
        elif sys.argv[2] == 'seq':      # count occurrences of number
            grid_total[line[i]] += 1

print grid_total

import Image

img = Image.new('L', (10,10))    # 8-bit pixels, black and white
img.putdata(grid_total, 255/max(grid_total))
img = img.resize((100,100))
img.save(sys.argv[1]+'.bmp')
img.show()

#!/usr/bin/python

import conf

if not conf.is_complete:
    print "conf is not complete, missing:", conf.missing
    exit(-1)

print "current conf:"
for c in conf.REQUIRED:
    print c, getattr(conf,c)

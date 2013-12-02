#!/bin/bash

if test -z "$PYTHON" ; then 
PYTHON=python
fi

# just checks if conf can be loaded automatically (env / filepath)
get_CWD ()
{
$PYTHON -c 'import os; print os.getcwd()'
}

get_python_version ()
{
$PYTHON -c 'import sys; print sys.version'
}

get_python_paths ()
{
$PYTHON -c 'import sys; print sys.path'
}

get_conf ()
{
$PYTHON -c 'from utils import conf;
conf.set_name("'$1'")
try:
 missing = conf.load()
except conf.LoadException, e:
 print "CONFIGURATION ERROR:", e[1], "(file: %s)" % e[0]
 exit(1)
print conf.get_loaded()
exit(0)'
}

# checks if there's missing definitions in the conf file
check_conf ()
{
$PYTHON -c 'from utils import conf;
conf.set_name("'$1'")
try:
 missing = conf.load()
except conf.LoadException, e:
 print "CONFIGURATION ERROR:", e[1], "(file: %s)" % e[0]
 print "candidate files:", conf.build_candidates()
 exit(1)
if missing:
 print "missing definitions", missing
 exit(1)
exit(0)'
}

# get search path and files checked for conf
get_conf_candidates ()
{
$PYTHON -c 'import conf;
conf.set_name("'$1'")
print " ".join(conf.build_candidates())'
}

# get backend
get_backend ()
{
$PYTHON -c 'from utils import conf;
conf.load(name="'$1'")
print conf.ROBOT["modules"][0]["backend"]'
}

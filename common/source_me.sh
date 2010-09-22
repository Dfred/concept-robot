# just checks if conf can be loaded automatically (env / filepath)
get_python_conf()
{
python -c 'import conf;
conf.NAME="'$1'"
try:
 missing = conf.load()
except conf.LoadException, e:
 print "CONFIGURATION ERROR:", e[1], "Last tried file:", e[0]
 exit(1)
print conf.LOADED_FILE
if missing:
 exit(1)
exit(0)'
[ $? = 0 ]
}

# checks if there's missing definitions in the conf file
check_python_conf()
{
python -c 'import conf;
conf.NAME="'$1'"
try:
 missing = conf.load()
except conf.LoadException, e:
 print "CONFIGURATION ERROR:", e[1], "Last tried file:", e[0]
 exit(1)
if missing:
 print "missing definitions", missing
 exit(1)
exit(0)'
[ "$?" = "0" ]
}

# get search path and files checked for conf
get_python_conf_candidates()
{
python -c 'import conf;
conf.NAME="'$1'"
print " ".join(conf.build_paths())'
}

# quick way to die on failure
check_exiting()
{
  if ! $1; then
	echo
	echo $2
	exit 1
  fi
}

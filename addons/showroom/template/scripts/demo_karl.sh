#!/usr/bin/env bash
# PARAMS:

function first_install {
# get the last version in svn (no release yet)
svn co http://osi.agendaless.com/bfgsvn/karlsample/trunk/ karl

# create a sandbox and run the buildout
virtualenv --no-site-packages --distribute -p python2.5 sandbox

cd karl

../sandbox/bin/python bootstrap.py
# remove the buildout-cache and download-cache params, then buildout
sed -i '/^eggs-directory/d;/^download-cache/d' buildout.cfg
bin/buildout -N

# change the listening port
sed -i "s/6543/$PORT/" -i etc/karl.ini
# change the ZEO port
sed -i "s/8886/$(($PORT+1000))/" -i etc/zeo.conf
sed -i "s/8886/$(($PORT+1000))/" -i etc/karl.ini

cd ..

# needed to be able to clone the virtualenv
virtualenv --no-site-packages --distribute -p python2.5 sandbox --relocatable

# create a unique startup script
cat > start.sh <<EOF
#!/bin/bash
trap "pkill -P \$\$" EXIT
cd karl
bin/runzeo -C etc/zeo.conf &
exec bin/paster serve etc/karl.ini
EOF

# create a howto for installation instruction
cat > howto.html << EOF
<p>The initial user account is<br/>
user : admin<br/>
pass : admin</p>
EOF
}

function reconfigure_clone {
# $1 is the old name, $2 is the old port
sed -i "s/$2/$PORT/" -i etc/karl.ini
sed -i "s/$(($2+1000))/$(($PORT+1000))/" -i etc/zeo.conf
sed -i "s/$(($2+1000))/$(($PORT+1000))/" -i etc/karl.ini

}

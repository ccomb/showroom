#!/usr/bin/env sh
set -e # explicit fail on errors
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT

# load vars and fonctions
. scripts/config.sh

! [ -d $DEMOS/$NAME ] && svn co http://osi.agendaless.com/bfgsvn/karlsample/trunk/ $DEMOS/$NAME
cd $DEMOS/$NAME

bin/virtualenv --no-site-packages --distribute .
bin/python ./bootstrap.py -d
bin/buildout -N buildout:eggs-directory=$HOME/eggs buildout:parts="karl flunc"
bin/supervisor

cat > daemon.sh << EOF
#!/usr/bin/env sh
$DEMOS/$NAME/bin/supervisorctl \$1
EOF
chmod +x daemon.sh

cd -

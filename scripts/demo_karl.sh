#!/usr/bin/env sh
set -e # explicit fail on errors
# gabriel pettier, for alterway solution
# 24/02/2010 11:03:42 (UTC+0100)

# PARAMS:NAME,COMMENT

# load vars and fonctions
. $SCRIPTS/config.sh

! [ -d $DEMOS/$NAME ] && svn co http://osi.agendaless.com/bfgsvn/karlsample/trunk/ $DEMOS/$NAME
cd $DEMOS/$NAME
rm -Rf etc && svn up

bootstrap

$BIN/virtualenv --no-site-packages --distribute .
bin/python bootstrap.py -d
bin/buildout -N buildout:eggs-directory=$HOME/eggs

ZEO_PORT=$(echo $PORT|perl -pe 's/^9/7/')
SUPERVISOR_PORT=$(echo $PORT|perl -pe 's/^9/6/')

perl -pe "s/8886/$ZEO_PORT/" -i etc/zeo.conf
perl -pe "s/8886/$ZEO_PORT/" -i etc/karl.ini
perl -pe "s/6543/$PORT/" -i etc/karl.ini
perl -pe "s/9037/$SUPERVISOR_PORT/" -i etc/supervisord.conf

perl -pe "s/pipeline:main/pipeline:karl_pipeline/" -i etc/karl.ini
cat >> etc/karl.ini << EOF

[app:main]
use = egg:Paste#urlmap
/$NAME = karl_pipeline

EOF


cat > daemon.sh << EOF
#!/usr/bin/env sh
cd $DEMOS/$NAME
case "\$1" in
  start)
    $DEMOS/$NAME/bin/supervisord
    ;;
  stop)
    $DEMOS/$NAME/bin/supervisorctl shutdown
    ;;
  *)
    $DEMOS/$NAME/bin/supervisorctl \$1 all
esac

EOF
chmod +x daemon.sh

cd -

#!/usr/bin/env sh
# config file for demos frontend

ZEO_PORT=$(echo $PORT|perl -pe 's/^9/7/')
SUPERVISOR_PORT=$(echo $PORT|perl -pe 's/^9/6/')

bootstrap () {
    wget -O bootstrap.py http://svn.zope.org/*checkout*/zc.buildout/trunk/bootstrap/bootstrap.py
}

supervisor_daemon_sh () {
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
}

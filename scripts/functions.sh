#!/bin/bash

function mysql_start {
    echo STARTING MYSQL
    # allow failing commands (while trying to connect)
    set +e
    
    # start mysql temporarily
    /usr/sbin/mysqld --no-defaults --socket=$PWD/mysql/mysqld.sock --datadir=$PWD/mysql/ --log-error=$PWD/mysql/mysql-error.log --port=$1 &
    
    # wait for mysql to be started
    echo "Waiting for mysql to start..."
    n=0
    mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root status
    while [ $? -ne 0 -a $n -lt 20 ]; do
        sleep 0.5; echo "Waiting for mysql to start..."
        n=$((n+1))
        mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root status
    done

    # forbid failing commands again
    set -e
}
export -f mysql_start


function mysql_stop {
    echo STOPPING MYSQL
    mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root shutdown
}
export -f mysql_stop


function mysql_create {
    # initialize MySQL
    mkdir mysql
    mysql_install_db --no-defaults --datadir=$PWD/mysql/

    # start mysql 
    mysql_start $2
    
    # create a database
    mysqladmin --socket=$PWD/mysql/mysqld.sock --user=root create $3
    
    # create a user with all privileges on the database
    echo "CREATE USER '$4'@'$1' IDENTIFIED BY '$5';" > mysql.tmp
    echo "GRANT ALL ON $4.* TO '$3'@'$1';" >> mysql.tmp
    echo "FLUSH PRIVILEGES;" >> mysql.tmp
    mysql --socket=$PWD/mysql/mysqld.sock --user=root mysql < mysql.tmp
    rm mysql.tmp
}
export -f mysql_create


function mysql_create_and_stop {
    mysql_create $1 $2 $3 $4 $5
    mysql_stop
}
export -f mysql_create_and_stop


#!/usr/bin/env sh
# config file for demos frontend

# no "/" at end of path!
BASE_URL="http://127.0.0.1"

get_free_port (){
    ! [ -f scripts/num_port.count ] && echo "90000" > scripts/num_port.count
    num=$(cat scripts/num_port.count)
    echo $((num+1)) > scripts/num_port.count
    echo $num
}


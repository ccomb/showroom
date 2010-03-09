#!/usr/bin/env sh
# config file for demos frontend

# no "/" at end of path!
VIRTUAL_ENV_PATH="~/demos_alterway/virtualenv"
DEMOS_BASE_DIR="~/demos_alterway/demos/"

BASE_URL="http://127.0.0.1"

get_free_port (){
    num=$(cat ./num_port.count)
    echo $((num+1)) > num_port.count
    echo $num
}


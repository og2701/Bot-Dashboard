#!/bin/bash

usage() {
    echo "Usage: $0 [-p password]"
    exit 1
}

while getopts ":p:" opt; do
    case $opt in
        p)
            LOGIN_PASSWORD=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done

if [ -z "$LOGIN_PASSWORD" ]; then
    echo "Password is required."
    usage
fi

CONFIG_CONTENT=$(cat <<EOF
class Config:
    GUILD_ID = 959493056242008184
    LOGIN_PASSWORD = '$LOGIN_PASSWORD'
EOF
)

echo "$CONFIG_CONTENT" > config.py

echo "config.py has been generated with the provided password."

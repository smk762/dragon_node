#!/bin/bash

if [ $# -eq 0 ]; then
    echo "No arguments provided. You need to add a valid branch as a parameter"
    echo "For example: ./update_dpow_branch.sh dev"
    exit 1
fi

echo "Existing submodule settings:"
git config --file=../.gitmodules -l
echo
echo "Updating submodule branch to $1"
git config --file=../.gitmodules submodule.dPoW.branch $1
git submodule sync
git submodule update --init --recursive --remote
echo
echo "Updated submodule settings:"
git config --file=../.gitmodules -l
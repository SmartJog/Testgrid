#!/bin/bash



for pkg in $PACKAGE; do
    if apt-get -qq install $pkg; then
	echo "Successfully installed $pkg"
    else
	echo "Error installing $pkg"
    fi
done
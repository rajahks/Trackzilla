#!/bin/bash

#Setup the UID and GID

echo "USERID=`id -u`"   > .env    # > overwrites the old content
echo "GROUPID=`id -g`" >> .env    # >> appends to the file

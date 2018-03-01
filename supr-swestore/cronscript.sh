#!/bin/sh

# Source init scripts.
. /etc/profile
LD_LIBRARY_PATH="/supr/lib64:/opt/rh/python27/root/usr/lib64"
export LD_LIBRARY_PATH

# Build virtual environment and call python script.
cd /supr
source bin/activate
python supr_swestore_main.py
if [ $? -ne 0 ]
then
	echo "Python script failed"
fi
deactivate


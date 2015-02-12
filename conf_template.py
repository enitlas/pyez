#!/usr/bin/python
import sys
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
import getpass
import os

# List of valid Juniper devices
dict = {}
dict['ip1'] = "host1"

# Define the device, give credentials
target_host = raw_input('device name: ')
userid = raw_input('username: ')
hidepass = getpass.getpass()
dev = Device(host=target_host, user=userid, password=hidepass)

dev.bind( cu=Config )

# Open the device, handle exceptions
try:
    dev.open()
except Exception as err:
    print "Cannot connect to device:", err
    quit()

# Define configuration file path, validate path and file extension
while True:
    conf_file = raw_input('configuration file location: ')
    if not os.path.exists(conf_file):
        print "File path is invalid, please enter a valid file path"
        continue
    elif not conf_file.endswith('.conf'):
        print "File is not a .conf file, please enter a .conf file"
        continue
    else:
        break

# merge configuration to candidate configuration
print "Loading configuration changes"
dev.cu.load(path=conf_file, merge=True)

# display candidate configuration for validation
print "Candidate configuration:"
dev.cu.pdiff()

# user commit confirmation, else rollback
commit_config = raw_input('Do you want to commit the configuration? ')
if commit_config in ["yes", "Yes", "y", "Y"]:
    print "Committing configuration"
    try:
        dev.cu.commit()
    except CommitError:
        print "Error: Unable to commit configuration"
        print "Rolling back configuration"
        dev.cu.rollback(rb_id=1)
        dev.cu.commit
else:
    print "Commit cancelled"
    print "Rolling back configuration"
    dev.cu.rollback(rb_id=1)
    dev.cu.commit()

# close netconf session
dev.close()

quit()

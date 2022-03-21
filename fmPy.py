#!/usr/bin/python3
# fmPy v1.0
########################
#
# This is a simple script to update or create a record in a FileMaker table using the data api_version
# It expects a Base64 encoded JSON array with the following:
#   action -> 'updateRecord' or 'createRecord' (for now, more to come)
#   pk -> updateRecord only - the field we need to search on (usually the primary key but doesn't need to be)
#   uuid -> updateRecord only - the value of the pk field above you want to update a record in (so, a means to identify the record)
#   serverName -> FQDN or IP of your server, however it needs to be. Ex: https://myserver.example.com
#   databaseName -> the solution name eg Inventory
#   layoutName -> Data API needs a layout.
#
# This file needs a file called fmInfo.py from which it will get :
#   the credentials for the server
#   some custom functions
# All the user-specific stuff is in fmInfo.py so you hopefully shouldn't need to edit anything here
#
# The idea is to invoke this script on your web server by using Insert From URL.
# The result will be "OK" if successful or an error if not.
#
# See FMPython.fmp12 for example code
#
# It's always a good idea to make sure your Data API user (the one in fmInfo.py) has as few rights as possible
#
# This uses the python-fmrest package by David Hamann
#   https://github.com/davidhamann/python-fmrest
#
# The repo for this is https://github.com/gibbsjoh/fmPy
#
########################

# We don't need this, it seems
print("Content-type: text/html\n\n")

# Import needed modules plus fmInfo
import requests
import fmrest
from fmrest.exceptions import FileMakerError
import json
import cgi
import base64
import fmInfo

# initialise error var
fmError = 'OK'

# This seems needed for the FMRest stuff
requests.packages.urllib3.disable_warnings()

# The encoded array is sent as part of the URL, so get it into the script
form = cgi.FieldStorage()
payloadRaw = form.getvalue('payloadData')

# Unencode the payload data
p = base64.b64decode(payloadRaw)
payloadData = p.decode('utf-8')

# debugging
#print(payloadData)
#exit()

# Convert the payload to JSON so Python can do things with it
formJSON = json.loads(payloadData)

# what are we doing?
action = formJSON['action']
# where are we doing it?
serverName = formJSON['serverName']
databaseName = formJSON['databaseName']
layoutName = formJSON['layoutName']

# Get our user creds
#   If you have different users for different files, change the userName variable to maybe userNameSolutionName
userName = fmInfo.userName
myPassword = fmInfo.myPassword

# Connnect to the FileMaker server
fms = fmrest.Server(serverName,
                user = userName,
                password = myPassword,
                database = databaseName,
                layout = layoutName,
                verify_ssl = False
        )
fms.login()

# What are we doing? Get the data element of the JSON array
fmPayload = formJSON['data']

# Get the keys (our fieldnames for FileMaker)
keys = fmPayload.keys()

#now we do something with it!
if (action == "createRecord"): #create a new record w/ values we've passed it.
    #print(action)
    f = {}
    for key in keys:
        # get the value for the field
        value = fmPayload[key]
        f[key] = value
        fmArray = f #json.dumps(f)
    
    try:
        record_id = fms.create_record(fmArray)
    except FileMakerError as createError:
        fmError = createError
    
elif (action == 'updateRecord'):
    #print(action)
    uuid = formJSON['uuid']
    pk = formJSON['pk']

    find_query = [{ pk : uuid}]
    try:
        foundset = fms.find(query=find_query)
    except FileMakerError as findError:
        fmError = findError
    record = foundset[0]
   
    for key in keys:
        value = fmPayload[key]
        record[key] = value
    
    try:
        fms.edit(record)
    except FileMakerError as updateError:
        fmError = updateError

# Be nice and close the DAPI connection
fms.logout()

# If an error occured, report back, otherwise result is OK
# You can check for this in FM by seeing if whatever field or var you used in Insert from URL is OK
if (fmError != 'OK'):
    print(fmError)
else:
    print('OK')







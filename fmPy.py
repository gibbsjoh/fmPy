#!/usr/bin/env python

# fmPy v1.15
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

# set timeout higher
fmrest.utils.TIMEOUT = 40

#initialise f array
f = {'foo':'bar'}

# This seems needed for the FMRest stuff
requests.packages.urllib3.disable_warnings()

# The encoded array is sent as part of the URL, so get it into the script
form = cgi.FieldStorage()
payloadRaw = form.getvalue('payloadData')

# Unencode the payload data
# first we see if it's already JSON and we just load it right in
try:
    formJSON = json.loads(payloadRaw)
except:
    p = base64.b64decode(payloadRaw)
    payloadData = p.decode('utf-8')
    formJSON = json.loads(payloadData)

# if (payloadRaw[0] == "{"):
#     #not encoded
#     notJSON = 1
#     payloadData = payloadRaw
# else:
#     notJSON = 0
#     p = base64.b64decode(payloadRaw)
#     payloadData = p.decode('utf-8')

# debugging
#print(payloadData)
#exit()

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

elif(action=='getRecord'):
    #Set up the query
    find_query = [fmPayload]
    try:
        #Perform the find
        foundset = fms.find(query=find_query,limit=20000)
    except FileMakerError as findError:
        fmError = findError

    returnArray = {}
    i = 0
    for r in foundset:
        thisRecord = foundset[i]
        f = {}
        keys = thisRecord.keys()
        for key in keys:
            # get the value for the field
            value = thisRecord[key]
            f[key] = value
        
        returnArray[i] = f
        i = i + 1
    
    returnArray = json.dumps(returnArray)

elif(action=='runScript'):
    # new! 31/03/22 run a script (requires a data set to find, for now using the pk/uuid method)
    uuid = formJSON['uuid']
    pk = formJSON['pk']

    # the API can take a parameter, for my use case we pass it a JSON array
    # specify the script in the data array as 'fmScript'
    # the parameter array is the 'data' array we use for getRecord usually
    fmScript = fmPayload['fmScript']

    #bug fix here v1.51 12-04-2022 to ensure proper JSON passed to script
    paramJSON = json.dumps(fmPayload)
    # need some form of error capture here!

    find_query = [{ pk : uuid}]
    try:
        foundset = fms.find(query=find_query,scripts={'after': [fmScript, paramJSON]})
        #1.51 added logic to catch the FMS script result.
        #the result is a touple with when it ran (eg after), the last FM error code, and what you passed with "exit script" in FM
        scriptResult = fms.last_script_result
        resultKeys = scriptResult.keys()

    except FileMakerError as findError:
        fmError = findError
    #record = foundset[0]

    
# Be nice and close the DAPI connection
fms.logout()

# If an error occured, report back, otherwise result is OK
# You can check for this in FM by seeing if whatever field or var you used in Insert from URL is OK
if (fmError != 'OK'):
    print(fmError)
elif(action=='getRecord'):
    print(returnArray)
elif(action=='runScript'):
    print('OK')
    print('FMS script result:',scriptResult)
else:
    print('OK')

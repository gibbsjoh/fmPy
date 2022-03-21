# fmPy
Python script to create or update records in FileMaker using the Data API.

** I am relatively new to Python and that probably shows in the code.
** This war written more from my own use and that of my team, but in the absence of any "plug n play" Python code to talk to FM in a generic way I figured I'd publish on here.

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
########################

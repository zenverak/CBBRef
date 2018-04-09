import os
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from copy import deepcopy as dc

SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'grabbing data from google sheets'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credentials =  None

    credential_path = os.path.join('..\\','client_secret.json')
##    print (credential_path)
##
##    return os.path.isfile(credential_path)
    absPath = os.path.abspath(credential_path)
    print(absPath)
    store = Storage(absPath)
    try:
        credentials = store.get()
    except:
        pass
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)


print (get_credentials())

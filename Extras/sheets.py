from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def return_data(service, ranges):
    spreadsheetId = '1xJOn_j64vTIispeuf59OD_8-i5AjYZFt36YKm1_XzmY'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=ranges).execute()
    values = result.get('values', [])
    return values



    
def get_values():
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    category_ranges = ['push','average','chew']

    free_throw_headers = ['Home', 'Away', 'Neutral']
    

    range_headers = 'A2:Z2'



    
    headers = return_data(service, range_headers)
    push_ranges_ranges = ['A{0}:Z{0}'.format(i) for i in range(3,12)]
    average_ranges_ranges = ['A{0}:Z{0}'.format(i) for i in range(15,23)]
    chew_ranges_ranges = ['A{0}:Z{0}'.format(i) for i in range(27,35)]

    free_throw_ranges = 'A39:C39'

    time_off_ranges = ['A{0}:C{0}'.format(i) for i in range(43,51)]

    push_values = [return_data(service, range_) for range_ in push_ranges_ranges]
    average_values = [return_data(service, range_) for range_ in average_ranges_ranges]
    chew_values = [return_data(service, range_) for range_ in chew_ranges_ranges]

    free_throw_values = return_data(service, free_throw_ranges)

    time_off_values = [return_data(service, range_) for range_ in time_off_ranges]

    

 


if __name__ == '__main__':
    get_values()

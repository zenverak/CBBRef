from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from copy import deepcopy as dc
##try:
##    import argparse
##    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
##except ImportError:
##    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'grabbing data from google sheets'

play_dict = {}
time_dict = {}

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

    free_throw_headers = ['home', 'away', 'neutral']
    

    range_headers = 'A2:Z2'



    
    headers = return_data(service, range_headers)
    push_ranges_ranges = ['A{0}:Z{0}'.format(i) for i in range(3,12)]
    average_ranges_ranges = ['A{0}:Z{0}'.format(i) for i in range(15,24)]
    chew_ranges_ranges = ['A{0}:Z{0}'.format(i) for i in range(27,36)]

    free_throw_ranges = 'A39:C39'

    time_off_ranges = ['A{0}:C{0}'.format(i) for i in range(43,52)]

    push_values = [return_data(service, range_) for range_ in push_ranges_ranges]
    average_values = [return_data(service, range_) for range_ in average_ranges_ranges]
    chew_values = [return_data(service, range_) for range_ in chew_ranges_ranges]

    free_throw_values = return_data(service, free_throw_ranges)

    time_off_values = [return_data(service, range_) for range_ in time_off_ranges]
    return headers, push_values, average_values, chew_values, free_throw_values, time_off_values

    

def format_head(head):
    return [h for h in head[0] if h!='']

def combine(plays):
    for play in plays:
        p = play[0]

def return_playdict():
    sub_dict = {'Attack the Rim':{
                        'Man':{},
                        'Zone':{},
                        'Press':{}
                        },
                'Midrange':{
                        'Man':{},
                        'Zone':{},
                        'Press':{}
                        },
                '3 Point':{
                        'Man':{},
                        'Zone':{},
                        'Press':{}
                        }
                }
    play_dict = {'push':{},
                 'average':{},
                 'chew':{},
                 'freeThrows':{'home':'','away':'','neutral':''}}
 
    for key in play_dict:
        if key == 'freeThrows':
            pass
        else:
            play_dict[key] = dc(sub_dict)
    return play_dict


def get_range_list(range_list):
    new_range_list = []
    new_range_list.append(range_list[0])
    new_range_list.append(range_list[1])
    i = 2
    while i < len(range_list):
        new_range_list.append([range_list[i],range_list[i+1]])
        i += 2
    return new_range_list

def combine_headers_with_list(range_list, headers):
    put_in_dict = {}
    for i in range(2, len(range_list)):
        range_ = range_list[i]
        key = '{}-{}'.format(range_[0],range_[1])
        head = headers[i]
        result = {'result':head}
        if head == 'Made 2pt' or head == 'Made 2pt and Foul':
            result['points'] = 2
        elif head == 'Made 3pt' or head == 'Made 3pt and Foul':
            result['points'] = 3
        put_in_dict[key] = result
    return put_in_dict

def add_to_dict(play_dict, type_, play_type, headers):
    for plays in play_type:
        play = plays[0]
        off_style = play[0]
        def_style = play[1]
        new_play = get_range_list(play)
        play_dict[type_][off_style][def_style] = combine_headers_with_list(new_play, headers)
    return play_dict

def setup_play_dict(head, push, ave, chew, free):

    play_dict = return_playdict()
    formatted_headers =  format_head(head)
    play_dict = add_to_dict(play_dict,'push',push, formatted_headers)
    play_dict = add_to_dict(play_dict,'average',ave, formatted_headers)
    play_dict = add_to_dict(play_dict,'chew',chew, formatted_headers)
    play_dict['freeThrows']['home'] = free[0][0]
    play_dict['freeThrows']['away'] = free[0][1]
    play_dict['freeThrows']['neutral'] = free[0][2]
    return play_dict

def get_play_type_name(type_):
    if type_ == 'Push Pace':
        return 'push'
    elif type_ == 'Average':
        return 'average'
    elif type_ == 'Chew Clock':
        return 'chew'
    else:
        return 'balls'

def get_time_dict(times):
    time_dict = {'Attack the Rim':{},
                 'Midrange':{},
                 '3 Point':{}
                 }
    for time in times:
        ##tfp = time for play
        tfp = time[0]
        play_style = tfp[0]
        play_type = get_play_type_name(tfp[1])
        time_dict[play_style][play_type] = int(tfp[2].replace(':',''))
    return time_dict
        
        
    
def get_all_dicts():
    global play_dict
    global time_dict
    head, push, ave, chew, free, time = get_values()
    play_dict = setup_play_dict(head, push, ave, chew,free)
    time_dict = get_time_dict(time)


if __name__ == '__main__':
    get_all_dicts()

    
    

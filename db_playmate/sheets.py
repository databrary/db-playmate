import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from data_model import Lab, Site

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
PLAY_MASTER_ID = '1V9RuZJNRN4lehLzRSWO0MqVclsXPw7Z-Lxq-VQOvM-A'
PLAY_MASTER_RANGE = 'SiteTracking!A2:X'
SITE_CODE_COL = ord('w') - 97
LAB_CODE_COL = ord('x') - 97
EMAIL_COL = ord('q') - 97
INST_COL = ord('a') - 97
PI_COL = ord('h') - 97
ROLE_COL = ord('b') - 97

def read_master():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('env/token.pickle'):
        with open('env/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'env/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('env/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=PLAY_MASTER_ID,
                                range=PLAY_MASTER_RANGE).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        labs = []
        sites = {}
        test_lab = Lab("TEST", "TEST", "TEST", "TEST", "TEST")
        test_lab.db_volume = "PLAY Databrary API"
        labs.append(test_lab)
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('%s, %s' % (row[INST_COL], row[LAB_CODE_COL]))
            site_code = row[SITE_CODE_COL]
            lab_code = row[LAB_CODE_COL]
            email = row[EMAIL_COL]
            inst = row[INST_COL]
            pi = row[PI_COL]
            role = row[ROLE_COL]
            if site_code not in sites:
                sites[site_code] = Site(site_code)
            if "Coding" in role:
                lab = Lab(site_code, lab_code, pi, email, inst)
                sites[site_code].labs[lab_code] = lab
                labs.append(lab)
        return sites, labs


if __name__ == '__main__':
    read_master()

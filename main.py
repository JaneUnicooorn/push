#for Googl API
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from flask import Flask
import config
import requests
import csv
from flask import request
from flask import jsonify




URL = f'https://api.telegram.org/bot{config.TOKEN}/'

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


app = Flask(__name__)


def connect_to_Google_API():

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    return service


def send_message(chat_id, text="Oh hi Johnny, I didn't know it was you"):

    answer = {
        'chat_id':chat_id,
        'text':text
    }

    r = requests.post(URL+'sendMessage', json=answer)

    return r.json()


def get_file_content(service):

    results = service.files().list(q='name = "f.csv"', fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    final_file_content = []

    if not items:
        print('No files found.')

    else:
        file_id = items[0]['id']
        file_content_in_bytes = service.files().get_media(fileId=file_id).execute()
        file_content_str = file_content_in_bytes.decode("utf-8", "strict") #strict

        file_content_lines = file_content_str.split('\n')[1:-1]

        for line in csv.reader(file_content_lines):
            final_file_content.append(line)

    return final_file_content


def push(file_content):

    for el in file_content:

        user_id = int(el[0])

        places = el[2].split(',')
        num_of_places = len(places)

        text = f'Нещодавно Ви шукали "{el[1]}". Додано {num_of_places} нових меню закладів, що пропонують {el[1]}. Ознайомитися можна за посиланнями: {el[2]}'


        send_message(user_id, text)


@app.route('/', methods=['POST', 'GET'])
def index():

    service = connect_to_Google_API()

    file_content = get_file_content(service)


    if len(file_content)>0:
        push(file_content)
    else:
        print('No files found.')

    return 'Hello Bot'



if __name__ == '__main__':
    app.run()


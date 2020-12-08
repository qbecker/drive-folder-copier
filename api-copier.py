from __future__ import print_function
import pickle
import os.path
import http
import sys
from flask import Flask, request, Response
from threading import Thread
from apiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import Flask, request
# https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/service-py
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials



def create_orginal_folder(folderid, destid, service):
    foo = service.files().get(fileId=folderid).execute()
    
    print(foo)
    file_metadata = {
        'name': foo['name'],
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [destid]
    }
    bar = service.files().create(body=file_metadata,fields='id').execute()
    print(bar)
    return bar['id']
    
    
def replicate(folderid, destid, service):
    results = service.files().list(
       q="'"+folderid+"' in parents",
       fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])
    
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(item)
            file_metadata = {
            'name': item['name'],
            'parents': [destid],
            'mimeType': item['mimeType']
            }
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                file = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
                replicate(item['id'], file['id'], service)
            else:
                file = service.files().copy(fileId=item['id'], body=file_metadata, fields='id', supportsAllDrives=True).execute()
            print(u'{0} ({1})'.format(item['name'], item['id']))

                
                
                
def copy_folder(sourceID, destID):
    service = get_service()
    dest = create_orginal_folder(sourceID, destID, service)
    replicate(sourceID, dest, service)
    
def get_service():
    scopes = ['https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config.get('service_account_path'), scopes=scopes)
              
    
    delegated_credentials = credentials.create_delegated(app.config.get('del_name'))
    
    
    # https://developers.google.com/drive/api/v3/quickstart/python
    service = build('drive', 'v3', credentials=delegated_credentials)
    return service
    
app = Flask(__name__)

@app.route('/copy', methods=['GET', 'POST'])
def get_query_string():
    fromID = request.args.get('from')
    toID = request.args.get('to')
    Thread(target = copy_folder, args=[fromID, toID]).start()
    return Response('OK',status=201, mimetype='application/json')

if __name__ == '__main__':
    app.config['del_name'] = 'your delegation name'
    app.config['service_account_path'] = './yourservicecreds.json'
    app.run(debug=True)

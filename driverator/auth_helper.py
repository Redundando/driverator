from google.oauth2 import service_account
from googleapiclient.discovery import build

class AuthenticationHelper:
    def __init__(self, service_account_file: str):
        self.service_account_file = service_account_file
        self.drive_service = None
        
    def authenticate(self):
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=scopes
        )
        self.drive_service = build('drive', 'v3', credentials=credentials)
        
    async def authenticate_async(self):
        self.authenticate()

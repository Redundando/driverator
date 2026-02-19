import os
from typing import Optional, List, Dict, Union
from pathlib import Path
from cacherator import JSONCache
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

try:
    from .auth_helper import AuthenticationHelper
except ImportError:
    from auth_helper import AuthenticationHelper

class Driverator(JSONCache):
    def __init__(
        self,
        service_account_file: str,
        file_id: Optional[str] = None,
        file_name: Optional[str] = None,
        folder_id: Optional[str] = None,
        folder_name: Optional[str] = None,
        clear_cache: bool = False,
        ttl: int = 7
    ):
        cache_id = f"driverator_{file_name or file_id or 'file'}"
        super().__init__(data_id=cache_id, directory="data/driverator", clear_cache=clear_cache, ttl=ttl)
        
        self.service_account_file = service_account_file
        self.file_id = file_id
        self.file_name = file_name
        self._folder_id = folder_id
        self._folder_name = folder_name
        self.auth_helper = AuthenticationHelper(service_account_file)
        
    async def initialize(self):
        await self.auth_helper.authenticate_async()
        
        if self._folder_name and not self._folder_id:
            self._folder_id = await self._find_folder_by_name(self._folder_name)
            if not self._folder_id:
                self._folder_id = await self._create_folder(self._folder_name)
        
        if self.file_name and not self.file_id:
            self.file_id = await self._find_file_by_name(self.file_name)
        
        if self.file_id and await self.exists():
            await self._load_metadata()
                
    @property
    def url(self) -> Optional[str]:
        if not hasattr(self, '_url') and self.file_id:
            self._url = f"https://drive.google.com/file/d/{self.file_id}/view"
        return getattr(self, '_url', None)
    
    @property
    def download_url(self) -> Optional[str]:
        if not hasattr(self, '_download_url') and self.file_id:
            self._download_url = f"https://drive.google.com/uc?export=download&id={self.file_id}"
        return getattr(self, '_download_url', None)
    
    @property
    def size(self) -> Optional[str]:
        return getattr(self, '_size', None)
    
    @property
    def mime_type(self) -> Optional[str]:
        return getattr(self, '_mime_type', None)
    
    @property
    def created_time(self) -> Optional[str]:
        return getattr(self, '_created_time', None)
    
    @property
    def modified_time(self) -> Optional[str]:
        return getattr(self, '_modified_time', None)
        
    async def _load_metadata(self):
        file = self.auth_helper.drive_service.files().get(
            fileId=self.file_id,
            fields='id, name, mimeType, size, createdTime, modifiedTime'
        ).execute()
        
        self.file_name = file.get('name')
        self._size = file.get('size')
        self._mime_type = file.get('mimeType')
        self._created_time = file.get('createdTime')
        self._modified_time = file.get('modifiedTime')
        self._url = f"https://drive.google.com/file/d/{self.file_id}/view"
        self._download_url = f"https://drive.google.com/uc?export=download&id={self.file_id}"
        self.json_cache_save()
    
    async def exists(self) -> bool:
        if not self.file_id:
            return False
        try:
            file = self.auth_helper.drive_service.files().get(
                fileId=self.file_id,
                fields='id, trashed'
            ).execute()
            return not file.get('trashed', False)
        except:
            return False
    
    async def _find_file_by_name(self, name: str) -> Optional[str]:
        query = f"name='{name}' and trashed=false and mimeType!='application/vnd.google-apps.folder'"
        
        if self._folder_id:
            query += f" and '{self._folder_id}' in parents"
        
        results = self.auth_helper.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id)'
        ).execute()
        
        files = results.get('files', [])
        return files[0]['id'] if files else None
    
    async def _create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> str:
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        elif self._folder_id:
            file_metadata['parents'] = [self._folder_id]
            
        folder = self.auth_helper.drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
        
    async def _find_folder_by_name(self, name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        elif self._folder_id:
            query += f" and '{self._folder_id}' in parents"
            
        results = self.auth_helper.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        return files[0]['id'] if files else None
        
    async def upload(self, local_path: str) -> None:
        file_path = Path(local_path)
        upload_name = self.file_name or file_path.name
        
        file_metadata = {'name': upload_name}
        
        if self._folder_id:
            file_metadata['parents'] = [self._folder_id]
            
        media = MediaFileUpload(local_path, resumable=True)
        
        file = self.auth_helper.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, mimeType, size, createdTime, modifiedTime'
        ).execute()
        
        self.file_id = file.get('id')
        self.file_name = file.get('name')
        self._size = file.get('size')
        self._mime_type = file.get('mimeType')
        self._created_time = file.get('createdTime')
        self._modified_time = file.get('modifiedTime')
        self._url = f"https://drive.google.com/file/d/{self.file_id}/view"
        self._download_url = f"https://drive.google.com/uc?export=download&id={self.file_id}"
        self.json_cache_save()
    
    async def update(self, local_path: str) -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        media = MediaFileUpload(local_path, resumable=True)
        
        file = self.auth_helper.drive_service.files().update(
            fileId=self.file_id,
            media_body=media,
            fields='id, name, mimeType, size, createdTime, modifiedTime'
        ).execute()
        
        self._size = file.get('size')
        self._mime_type = file.get('mimeType')
        self._modified_time = file.get('modifiedTime')
        self.json_cache_save()
        
    async def download(self, local_path: str) -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        request = self.auth_helper.drive_service.files().get_media(fileId=self.file_id)
        
        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
    
    async def rename(self, new_name: str) -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        file_metadata = {'name': new_name}
        
        self.auth_helper.drive_service.files().update(
            fileId=self.file_id,
            body=file_metadata
        ).execute()
        
        self.file_name = new_name
        self.json_cache_save()
    
    async def move(self, folder_id: Optional[str] = None, folder_name: Optional[str] = None) -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        target_folder = folder_id
        if folder_name and not target_folder:
            target_folder = await self._find_folder_by_name(folder_name)
            if not target_folder:
                target_folder = await self._create_folder(folder_name)
        
        if not target_folder:
            raise ValueError("Must provide folder_id or folder_name")
        
        file = self.auth_helper.drive_service.files().get(
            fileId=self.file_id,
            fields='parents'
        ).execute()
        
        previous_parents = ",".join(file.get('parents', []))
        
        self.auth_helper.drive_service.files().update(
            fileId=self.file_id,
            addParents=target_folder,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        
        self._folder_id = target_folder
        if folder_name:
            self._folder_name = folder_name
        self.json_cache_save()
    
    async def delete(self, permanent: bool = False) -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        if permanent:
            self.auth_helper.drive_service.files().delete(fileId=self.file_id).execute()
        else:
            file_metadata = {'trashed': True}
            self.auth_helper.drive_service.files().update(
                fileId=self.file_id,
                body=file_metadata
            ).execute()
        
    async def share(
        self,
        email_addresses: Union[str, List[str]],
        role: str = 'reader'
    ) -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        if isinstance(email_addresses, str):
            email_addresses = [email_addresses]
            
        for email in email_addresses:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            self.auth_helper.drive_service.permissions().create(
                fileId=self.file_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            
    async def set_anyone_access(self, role: str = 'reader') -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        permission = {
            'type': 'anyone',
            'role': role
        }
        self.auth_helper.drive_service.permissions().create(
            fileId=self.file_id,
            body=permission
        ).execute()
    
    async def list_permissions(self) -> List[Dict]:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        results = self.auth_helper.drive_service.permissions().list(
            fileId=self.file_id,
            fields='permissions(id, type, role, emailAddress)'
        ).execute()
        
        return results.get('permissions', [])
    
    async def remove_permission(self, email_address: str) -> None:
        if not self.file_id:
            raise ValueError("No file_id set. Call initialize() or upload() first.")
        
        permissions = await self.list_permissions()
        
        for perm in permissions:
            if perm.get('emailAddress') == email_address:
                self.auth_helper.drive_service.permissions().delete(
                    fileId=self.file_id,
                    permissionId=perm['id']
                ).execute()
                return
        
        raise ValueError(f"No permission found for {email_address}")

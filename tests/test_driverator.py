import pytest
import os
from driverator import Driverator

SERVICE_ACCOUNT = 'service-account-key.json'
TEST_FOLDER = 'Driverator Pytest'

@pytest.fixture
def test_file():
    """Create a test file"""
    filename = 'pytest_test.txt'
    with open(filename, 'w') as f:
        f.write('Test content')
    yield filename
    if os.path.exists(filename):
        os.remove(filename)

@pytest.fixture
def updated_file():
    """Create an updated test file"""
    filename = 'pytest_updated.txt'
    with open(filename, 'w') as f:
        f.write('Updated content')
    yield filename
    if os.path.exists(filename):
        os.remove(filename)

@pytest.fixture
async def uploaded_file(test_file):
    """Upload a file and return the Driverator instance"""
    file = Driverator(
        SERVICE_ACCOUNT,
        file_name='pytest_upload.txt',
        folder_name=TEST_FOLDER
    )
    await file.initialize()
    await file.upload(test_file)
    yield file
    # Cleanup: delete file after test
    try:
        await file.delete(permanent=True)
    except:
        pass

class TestInitialization:
    @pytest.mark.asyncio
    async def test_initialize_basic(self):
        file = Driverator(SERVICE_ACCOUNT)
        await file.initialize()
        assert file.auth_helper.drive_service is not None
    
    @pytest.mark.asyncio
    async def test_initialize_with_folder(self):
        file = Driverator(SERVICE_ACCOUNT, folder_name=TEST_FOLDER)
        await file.initialize()
        assert file._folder_id is not None

class TestUpload:
    @pytest.mark.asyncio
    async def test_upload_file(self, test_file):
        file = Driverator(
            SERVICE_ACCOUNT,
            file_name='test_upload.txt',
            folder_name=TEST_FOLDER
        )
        await file.initialize()
        await file.upload(test_file)
        
        assert file.file_id is not None
        assert file.file_name == 'test_upload.txt'
        assert file.size is not None
        assert file.mime_type is not None
        
        await file.delete(permanent=True)
    
    @pytest.mark.asyncio
    async def test_upload_custom_name(self, test_file):
        file = Driverator(
            SERVICE_ACCOUNT,
            file_name='custom_name.txt',
            folder_name=TEST_FOLDER
        )
        await file.initialize()
        await file.upload(test_file)
        
        assert file.file_name == 'custom_name.txt'
        
        await file.delete(permanent=True)

class TestProperties:
    @pytest.mark.asyncio
    async def test_url_property(self, uploaded_file):
        assert uploaded_file.url is not None
        assert 'drive.google.com' in uploaded_file.url
        assert uploaded_file.file_id in uploaded_file.url
    
    @pytest.mark.asyncio
    async def test_download_url_property(self, uploaded_file):
        assert uploaded_file.download_url is not None
        assert 'export=download' in uploaded_file.download_url
        assert uploaded_file.file_id in uploaded_file.download_url
    
    @pytest.mark.asyncio
    async def test_metadata_properties(self, uploaded_file):
        assert uploaded_file.size is not None
        assert uploaded_file.mime_type is not None
        assert uploaded_file.created_time is not None
        assert uploaded_file.modified_time is not None

class TestFileOperations:
    @pytest.mark.asyncio
    async def test_exists(self, uploaded_file):
        exists = await uploaded_file.exists()
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_nonexistent(self):
        file = Driverator(SERVICE_ACCOUNT, file_id='nonexistent_id')
        await file.initialize()
        exists = await file.exists()
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_download(self, uploaded_file):
        download_path = 'pytest_downloaded.txt'
        await uploaded_file.download(download_path)
        
        assert os.path.exists(download_path)
        with open(download_path, 'r') as f:
            content = f.read()
            assert content == 'Test content'
        
        os.remove(download_path)
    
    @pytest.mark.asyncio
    async def test_update(self, uploaded_file, updated_file):
        old_size = uploaded_file.size
        await uploaded_file.update(updated_file)
        
        assert uploaded_file.size != old_size
    
    @pytest.mark.asyncio
    async def test_rename(self, uploaded_file):
        new_name = 'pytest_renamed.txt'
        await uploaded_file.rename(new_name)
        
        assert uploaded_file.file_name == new_name
    
    @pytest.mark.asyncio
    async def test_move(self, uploaded_file):
        await uploaded_file.move(folder_name='Driverator Pytest Archive')
        
        assert uploaded_file._folder_id is not None

class TestFindFile:
    @pytest.mark.asyncio
    async def test_find_by_name(self, uploaded_file):
        file_id = uploaded_file.file_id
        
        found_file = Driverator(
            SERVICE_ACCOUNT,
            file_name='pytest_upload.txt',
            folder_name=TEST_FOLDER
        )
        await found_file.initialize()
        
        assert found_file.file_id == file_id
    
    @pytest.mark.asyncio
    async def test_load_by_id(self, uploaded_file):
        file_id = uploaded_file.file_id
        file_name = uploaded_file.file_name
        
        loaded_file = Driverator(SERVICE_ACCOUNT, file_id=file_id)
        await loaded_file.initialize()
        
        assert loaded_file.file_name == file_name

class TestSharing:
    @pytest.mark.asyncio
    async def test_share_with_user(self, uploaded_file):
        await uploaded_file.share('arved.kloehn@gmail.com', role='reader')
        
        permissions = await uploaded_file.list_permissions()
        emails = [p.get('emailAddress') for p in permissions]
        assert 'arved.kloehn@gmail.com' in emails
    
    @pytest.mark.asyncio
    async def test_set_anyone_access(self, uploaded_file):
        await uploaded_file.set_anyone_access(role='reader')
        
        permissions = await uploaded_file.list_permissions()
        types = [p.get('type') for p in permissions]
        assert 'anyone' in types
    
    @pytest.mark.asyncio
    async def test_list_permissions(self, uploaded_file):
        permissions = await uploaded_file.list_permissions()
        
        assert isinstance(permissions, list)
        assert len(permissions) > 0
    
    @pytest.mark.asyncio
    async def test_remove_permission(self, uploaded_file):
        await uploaded_file.share('arved.kloehn@gmail.com', role='reader')
        await uploaded_file.remove_permission('arved.kloehn@gmail.com')
        
        permissions = await uploaded_file.list_permissions()
        emails = [p.get('emailAddress') for p in permissions]
        assert 'arved.kloehn@gmail.com' not in emails

class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_trash(self, test_file):
        file = Driverator(
            SERVICE_ACCOUNT,
            file_name='test_delete_trash.txt',
            folder_name=TEST_FOLDER
        )
        await file.initialize()
        await file.upload(test_file)
        
        await file.delete(permanent=False)
        exists = await file.exists()
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_delete_permanent(self, test_file):
        file = Driverator(
            SERVICE_ACCOUNT,
            file_name='test_delete_permanent.txt',
            folder_name=TEST_FOLDER
        )
        await file.initialize()
        await file.upload(test_file)
        
        await file.delete(permanent=True)
        exists = await file.exists()
        
        assert exists is False

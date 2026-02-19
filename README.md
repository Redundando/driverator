# Driverator

A Python library for Google Drive file operations with built-in caching and async support.

## Features

- File-centric design: each instance represents one file
- Upload, download, and update files
- Rename and move files between folders
- Delete files (trash or permanent)
- Share files with users or make public
- Manage permissions (list and remove)
- Automatic file discovery by name
- Check if file exists
- Persistent caching for metadata and URLs
- Async API

## Installation

```bash
pip install driverator
```

## Quick Start

```python
import asyncio
from driverator import Driverator

async def main():
    # Create file instance and upload
    file = Driverator(
        'path/to/service-account-key.json',
        file_name='report.pdf',
        folder_name='My Project'
    )
    await file.initialize()
    await file.upload('local_report.pdf')
    
    # Share file
    await file.share('user@example.com', role='writer')
    
    # Access file properties
    print(f"File URL: {file.url}")
    print(f"File size: {file.size} bytes")
    print(f"MIME type: {file.mime_type}")
    
    # Download file
    await file.download('downloaded_report.pdf')

asyncio.run(main())
```

## Advanced Usage

### Update File Content

```python
# Update existing file with new content
await file.update('updated_report.pdf')
print(f"Updated size: {file.size} bytes")
```

### Rename and Move

```python
# Rename file
await file.rename('Q1_report.pdf')

# Move to different folder
await file.move(folder_name='Archive')
```

### Manage Permissions

```python
# List all permissions
permissions = await file.list_permissions()
for perm in permissions:
    print(f"{perm['emailAddress']}: {perm['role']}")

# Remove specific permission
await file.remove_permission('user@example.com')
```

### Delete Files

```python
# Move to trash
await file.delete(permanent=False)

# Permanent delete
await file.delete(permanent=True)
```

### Check File Existence

```python
if await file.exists():
    print("File exists and is not trashed")
```

## Working with Existing Files

```python
# By file ID
file = Driverator('service-account-key.json', file_id='abc123...')
await file.initialize()
print(file.file_name)  # Loads metadata from Drive

# By file name (searches in folder)
file = Driverator(
    'service-account-key.json',
    file_name='report.pdf',
    folder_name='My Project'
)
await file.initialize()  # Finds existing file or ready to upload
```

## API Reference

### Driverator

**Constructor:**
- `service_account_file`: Path to service account JSON
- `file_id`: Optional file ID for existing file
- `file_name`: Optional file name (finds or creates)
- `folder_id`: Optional folder ID to work within
- `folder_name`: Optional folder name (finds or creates)
- `clear_cache`: Clear existing cache
- `ttl`: Cache time-to-live in days

**Methods:**
- `async initialize()`: Initialize and authenticate
- `async upload(local_path)`: Upload file to Drive
- `async update(local_path)`: Update/replace file content
- `async download(local_path)`: Download file from Drive
- `async rename(new_name)`: Rename the file
- `async move(folder_id=None, folder_name=None)`: Move to different folder
- `async delete(permanent=False)`: Delete file (trash or permanent)
- `async exists()`: Check if file exists (and not trashed)
- `async share(email_addresses, role='reader')`: Share with users
- `async set_anyone_access(role='reader')`: Make publicly accessible
- `async list_permissions()`: List all permissions
- `async remove_permission(email_address)`: Revoke user access

**Properties:**
- `url`: Shareable view URL
- `download_url`: Direct download URL
- `file_id`: Google Drive file ID
- `file_name`: File name
- `size`: File size in bytes
- `mime_type`: MIME type
- `created_time`: Creation timestamp
- `modified_time`: Last modified timestamp

## License

MIT License

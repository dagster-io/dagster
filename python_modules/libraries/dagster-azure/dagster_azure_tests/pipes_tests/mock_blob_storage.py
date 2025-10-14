import shutil
from pathlib import Path
from io import BytesIO

class MockBlobServiceClient:
    """We use this mock class to test AzureBlobStorage ContextInjector and MessageWriter.
    Because both the dagster orchestrator and the external process need to have the same view of the storage data,
    it is backed in a temporary directory on the local machine.
    """
    def __init__(self, temp_dir: str, storage_account: str):
        self._temp_dir = temp_dir
        self._storage_account = storage_account

    def get_container_client(self, container: str):
        return MockBlobContainerClient(
            self._temp_dir,
            self._storage_account,
            container
        )

    def get_blob_client(self, container: str, blob: str):
        return self.get_container_client(container).get_blob_client(blob)

    def cleanup(self):
        """Deletes all data created by the MockBlobServiceClient"""
        shutil.rmtree(
            Path(self._temp_dir).joinpath(self._storage_account),
            ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
        

class MockBlobContainerClient:
    def __init__(self, temp_dir: str, storage_account: str, container: str):
        self._temp_dir = temp_dir
        self._storage_account = storage_account
        self._container = container

    def get_blob_client(self, blob_key: str):
        return MockBlobClient(self._temp_dir, self._storage_account, self._container, blob_key)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
        

class MockBlobClient:
    def __init__(self, temp_dir: str, storage_account: str, container: str, blob: str):
        self._temp_dir = temp_dir
        self._storage_account = storage_account
        self._container = container
        self._blob = blob

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def upload_blob(self, data): # data can be bytes or str
        if isinstance(data, str):
            data = data.encode()
        blob_path = Path(self._temp_dir)/self._storage_account/self._container/self._blob
        blob_path.parent.mkdir(parents=True)
        blob_path.write_bytes(data)
    
    def download_blob(self):
        """Returns an object with a readall() method that returns bytes."""
        blob_path = Path(self._temp_dir)/self._storage_account/self._container/self._blob
        data = blob_path.read_bytes()
        
        return BytesIOWithReadAll(data) # Return a BytesIO object which has readall() method

    def exists(self):
        blob_path = Path(self._temp_dir)/self._storage_account/self._container/self._blob
        return blob_path.exists()

    def delete_blob(self):
        blob_path = Path(self._temp_dir)/self._storage_account/self._container/self._blob
        blob_path.unlink()


class BytesIOWithReadAll(BytesIO):
    def readall(self):
        return self.read()
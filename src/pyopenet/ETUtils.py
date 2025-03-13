from google.cloud import storage
from pathlib import Path
from google.oauth2 import (
    service_account,
)  # https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.credentials.html
from .ETJob import ETJob
from typing import Any

import json
import logging
import pandas as pd
import sys

def parse_geo(series_like_obj: pd.Series) -> pd.Series:
    return pd.Series([json.loads(row) for row in series_like_obj])

class CloudStorage:
    def __init__(self, project_id, credentials=None, logger=None):
        self.__project_id__ = project_id
        self.__credentials__ = credentials
        
        self.__logger__ = logging.getLogger(__name__)
        if logger:
            self.__logger__ = logger
        
        if credentials:
            self.__client__ = storage.Client(
                project=self.__project_id__, credentials=credentials
            )
        else:
            self.__client__ = storage.Client(project=self.__project_id__)

    @property
    def client(self) -> storage.Client:
        return self.__client__

    @property
    def project_id(self) -> str:
        return self.__project_id__

    @property
    def bucket(self) -> storage.Bucket:
        return self.client.get_bucket("forecasting-temp")
    
    @property
    def Credentials(self) -> service_account.Credentials | str:
        return self.__credentials__
    
    @Credentials.setter
    def Credentials(self, credentials: service_account.Credentials):
        self.__credentials__ = credentials
        return self
    
    def authenticated(self) -> bool:
        if isinstance(self.__credentials__, service_account.Credentials):
            return self.__credentials__.valid
        
        return False

    def fetch_save(self, fetch: ETJob, file_path: str, parents: bool = False) -> storage.Blob:
        """Exports ETFetch to csv and uploads bytes to storage client.

        Parameters
        ----------
        fetch : ETFetch
            The data runner object
        file_path : str
            Path to export file to.
        parents : bool, optional
            If True, creates parent folders for file_path if not already existing, by default False

        Returns
        -------
        storage.Blob
            Blob object that was written to.
        """
        
        # Locally, save to data/ sub-folder
        local_path = Path(f"data/{file_path}.csv")
        
        if parents and not local_path.parent.exists():
            local_path.parent.mkdir(parents=True)
        
        fetch.export(f'data/{file_path}')
        
        try:
            return self.pd_write(file_path, fetch.export())
        except Exception as err:
            if self.__logger__:
                self.__logger__.warning("Could not upload to StorageClient: ", err)
    
    def pd_write(self, blob_name: str, data: Any, **kwargs) -> storage.Blob:
        # Creates GCS object
        blob = self.bucket.blob(blob_name)

        with blob.open("w") as file:
            if isinstance(data, pd.DataFrame):
                file.write(data.to_csv(**kwargs))
            else:
                file.write(data)
            
            if self.__logger__:
                self.__logger__.info(
                    f"Wrote {sys.getsizeof(data)} bytes to {blob.name} in {self.bucket.name}"
                )
        return blob

    def pd_read(self, blob_name: str, **kwargs) -> pd.DataFrame:
        blob = self.bucket.blob(blob_name)

        with blob.open("r") as file:
            return pd.read_csv(file, **kwargs)

class Authenticate:
    def __new__(self, path_or_str):
        if Path(path_or_str).exists():
            return service_account.Credentials.from_service_account_file(path_or_str)
        
        try:
            return service_account.Credentials.from_service_account_info(path_or_str)
        except Exception as err:
            print("Could not form GoogleAuth Credentials object.\nError: " + str(err))
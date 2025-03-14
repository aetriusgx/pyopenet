from pyopenet.ETUtils import CloudStorage

from gcp_storage_emulator.server import Server
from google.cloud.storage import Client

from collections.abc import Generator

import os
import pytest
import requests
import tempfile

def create_gcp_client(http, **kwargs) -> Client:
    os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:9023"
    
    return Client(
        project=kwargs.get('project', "TEST"),
        _http=http,
        client_options={
            "api_endpoint": os.environ["STORAGE_EMULATOR_HOST"]
        }
    )

@pytest.fixture(scope="module")
def module_patch() -> Generator[pytest.MonkeyPatch, None, None]:
    with pytest.MonkeyPatch.context() as m:
        yield m

@pytest.fixture(scope="package")
def session_setup() -> Generator[requests.Session, None, None]:
    session = requests.Session()
    
    yield session

@pytest.fixture(scope="module")
def gcp_server_mock(module_patch, session_setup) -> Generator[tuple[Server, CloudStorage], None, None]:
    server_session = session_setup
    storage_client = CloudStorage("openet")
    # Overwrite the client in storage_client
    module_patch.setattr(
        storage_client,
        "__client__",
        create_gcp_client(server_session, project="openet"),
    )

    """Create server on localhost:9023 that stores written data in memory with a pre-configured bucket"""
    with Server(
        "localhost", 9023, in_memory=True, default_bucket="forecast_temp"
    ) as server:
        yield server, storage_client
    

@pytest.fixture(scope="module")
def cleandir() -> Generator[str, None, None]:
    """Creates temporary directory for use in testing\
        Yields original value of os.getcwd()
    """
    with tempfile.TemporaryDirectory() as tempdir:
        original_cwd = os.getcwd()  # copy current cwd
        os.chdir(tempdir)           # change cwd to tempdir
        yield original_cwd
        # --> Teardown Code <-- #
        os.chdir(original_cwd)
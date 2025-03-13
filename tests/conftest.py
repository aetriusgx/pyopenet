import importlib
import pyopenet
import pytest

assert pyopenet.__version__ == importlib.metadata.version()

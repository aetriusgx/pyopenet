from pyopenet.ETRequest import Request

import logging
import pytest
import requests

from dotenv import dotenv_values
from requests.exceptions import Timeout

def ETRequest_successful(requests_mock):
    res = Request(
        endpoint='https://developer.openet.org/awesome_endpoint',
        params={"param": "val"},
        key='1234567890'
    )
    
    requests_mock.post(res.endpoint, status_code=200)
    
    res.send()
    
    assert res.success() is True # Making it explicit for sanity check

def ETRequest_unsuccessful(requests_mock, monkeypatch):
    res = Request(
        endpoint="https://developer.openet.org/awesome_endpoint",
        params={"param": "val"},
        key="1234567890",
    )
    
    requests_mock.post(res.endpoint, status_code=403)
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    
    res.send()
    
    assert res.success() is False

def ETRequest_retry_successful(requests_mock):
    res = Request(
        endpoint="https://developer.openet.org/awesome_endpoint",
        params={"param": "val"},
        key="1234567890",
    )
    
    requests_mock.post(res.endpoint, [{'status_code': 403}, {'status_code': 200}])
    
    res.send()
    
    assert res._attempt == 2            # Initial value is 1.
    assert res.success() is True        # Explicit for sanity check.
    
def ETRequest_prompt_successful(requests_mock, monkeypatch):
    res = Request(
        endpoint="https://developer.openet.org/awesome_endpoint",
        params={"param": "val"},
        key="1234567890",
    )

    requests_mock.post(res.endpoint, [ {"status_code": 403}, {"status_code": 403}, {"status_code": 403},{"status_code": 200}])
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    
    res.send()
    
    assert res.success() is True

def ETRequest_timed_out(caplog, requests_mock):
    res = Request(
        endpoint="https://developer.openet.org/awesome_endpoint",
        params={"param": "val"},
        key="1234567890",
        logger=logging.getLogger(__name__),
    )
    
    assert type(res.endpoint) is str
    
    requests_mock.post(res.endpoint, response_list=[{"exc": Timeout}, {"status_code": 200}])
    
    res.send()
    
    assert res.success() is True
    assert res._attempt == 2
    assert "Request timed out." in caplog.text

def ETRequest_keyboard_interrupt(requests_mock):
    res = Request(
        endpoint="https://developer.openet.org/awesome_endpoint",
        params={"param": "val"},
        key="1234567890",
    )
    
    assert type(res.endpoint) is str
    
    requests_mock.post(res.endpoint, response_list=[{"exc": KeyboardInterrupt}])
    
    res.send()
    
    assert not res.success()

def ETRequest_bad_connection(requests_mock, monkeypatch):
    res = Request(
        endpoint="https://developer.openet.org/awesome_endpoint",
        params={"param": "val"},
        key="1234567890",
    )
    
    assert type(res.endpoint) is str
    
    requests_mock.post(res.endpoint, response_list=[{"exc": requests.exceptions.ConnectionError}])
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    
    res.send()
    
    assert not res.success()
    assert res._attempt == 4    # Exhausted all retries.

def ETRequest_missing_attributes():
    with pytest.raises(AttributeError) as endpoint_err:
        Request().send()
    assert "Request has no endpoint." in str(endpoint_err.value)
    
    with pytest.raises(AttributeError) as params_err:
        Request(endpoint="https://developer.openet.org/awesome_endpoint").send()
    assert "Request has no parameters." in str(params_err.value)
    
    with pytest.raises(AttributeError) as key_err:
        Request(endpoint="https://developer.openet.org/awesome_endpoint", 
                params={"param": "val"}).send()
    assert "Request has no API key." in str(key_err.value)
    

###--- Stress Test ---###
@pytest.mark.skipif(
    not requests.get("https://openet-api.org").status_code == 200,
    reason="No internet connection.",
)
def ETRequest_stress(monkeypatch, cleandir):
    KEY = dotenv_values(f"{cleandir}/.env").get('ET_KEY')
    if not KEY:
        pytest.skip("No API key found. Check repo config.")
    
    fields = [
        [
            -119.26424938,
            35.029047982,
            -119.264235993,
            35.028517411,
            -119.264222605,
            35.026751608,
            -119.264137936,
            35.025721516,
            -119.26393278,
            35.025712596,
            -119.26391496,
            35.025489623,
            -119.264048746,
            35.025387057,
            -119.259968617,
            35.025427246,
            -119.259817006,
            35.025543187,
            -119.259888379,
            35.028856251,
            -119.259977572,
            35.029114922,
            -119.264182532,
            35.029065819,
            -119.26424938,
            35.029047982,
        ],
        [
            -119.582950266,
            35.448056332,
            -119.58282093,
            35.447935987,
            -119.582624715,
            35.447940446,
            -119.582330481,
            35.447989438,
            -119.579084218,
            35.44893035,
            -119.574103434,
            35.448952629,
            -119.57408114,
            35.44899273,
            -119.574032039,
            35.452354904,
            -119.574072204,
            35.452390622,
            -119.576734247,
            35.452381681,
            -119.582883386,
            35.452381685,
            -119.582905679,
            35.452372728,
            -119.582950266,
            35.448056332,
        ],
        [
            -119.140821499,
            35.449006139,
            -119.140674293,
            35.448850103,
            -119.139229556,
            35.448832221,
            -119.13790078,
            35.448792116,
            -119.1366121,
            35.448814379,
            -119.136415909,
            35.449046246,
            -119.136384674,
            35.450999335,
            -119.136331167,
            35.452337075,
            -119.136326731,
            35.453019349,
            -119.136282097,
            35.453951255,
            -119.136246426,
            35.455721545,
            -119.136357876,
            35.455931158,
            -119.140616351,
            35.455935593,
            -119.140656458,
            35.455904361,
            -119.140687692,
            35.455074998,
            -119.140727798,
            35.452970303,
            -119.140821499,
            35.449006139,
        ],
        [
            -119.507323942,
            36.499708551,
            -119.507002822,
            36.499699695,
            -119.506989457,
            36.500337311,
            -119.507319427,
            36.500337286,
            -119.507323942,
            36.499708551,
        ],
        [
            -118.976574985,
            35.136293838,
            -118.976561572,
            35.132945088,
            -118.976539277,
            35.13291829,
            -118.974733321,
            35.132945039,
            -118.972655349,
            35.132998563,
            -118.970153805,
            35.133016425,
            -118.969288768,
            35.133052074,
            -118.967821711,
            35.13308774,
            -118.967839567,
            35.13638306,
            -118.967973348,
            35.136481102,
            -118.970693362,
            35.136441011,
            -118.97248151,
            35.13639196,
            -118.973823718,
            35.136369646,
            -118.976574985,
            35.136293838,
        ],
        [
            -119.474545075,
            35.472024005,
            -119.47448266,
            35.471756445,
            -119.474357742,
            35.471613789,
            -119.470438219,
            35.471618221,
            -119.4702376,
            35.471631629,
            -119.470242027,
            35.475279137,
            -119.470273191,
            35.478681483,
            -119.471477161,
            35.478681472,
            -119.472199592,
            35.478663606,
            -119.47454056,
            35.478668112,
            -119.474545075,
            35.472024005,
        ],
        [
            -119.925516273,
            36.82548159,
            -119.925467207,
            36.825075811,
            -119.924557544,
            36.825080295,
            -119.924566457,
            36.825490502,
            -119.925516273,
            36.82548159,
        ],
        [
            -119.163669942,
            35.266236522,
            -119.163643149,
            35.263556598,
            -119.163576256,
            35.263494196,
            -119.16318829,
            35.263480818,
            -119.15695897,
            35.263480746,
            -119.155086123,
            35.263525387,
            -119.154939019,
            35.263717099,
            -119.154921186,
            35.267065865,
            -119.155701506,
            35.26706146,
            -119.161707926,
            35.267061449,
            -119.161739155,
            35.266784939,
            -119.162889575,
            35.266807285,
            -119.163237352,
            35.266700226,
            -119.163598524,
            35.266459484,
            -119.163669942,
            35.266236522,
        ],
        [
            -118.949401176,
            35.082187083,
            -118.946502744,
            35.081964191,
            -118.944228666,
            35.081825931,
            -118.944068121,
            35.081808117,
            -118.944068121,
            35.083350924,
            -118.944090422,
            35.083404464,
            -118.944687908,
            35.083404442,
            -118.947015553,
            35.082713281,
            -118.948701094,
            35.082240611,
            -118.949401176,
            35.082280749,
            -118.949401176,
            35.082187083,
        ],
        [
            -118.873083686,
            36.061151554,
            -118.872347884,
            36.060616453,
            -118.871986737,
            36.060817085,
            -118.87241926,
            36.06153505,
            -118.872994445,
            36.061548376,
            -118.873083686,
            36.061151554,
        ],
    ]
    
    # Sets input to yes.
    monkeypatch.setattr("builtins.input", lambda _: "n")
    
    for field in fields:
        req = Request(
            endpoint="https://developer.openet-api.org/raster/timeseries/polygon",
            params={
                "date_range": ["2022-01-01", "2022-12-31"],
                "file_format": "JSON",
                "geometry": field,
                "interval": "monthly",
                "model": "SSEBop",
                "reducer": "mean",
                "reference_et": "gridMET",
                "units": "mm",
                "variable": "ET",
            },
            key=KEY
        )
        
        req.send()
        
        assert req.success() is True
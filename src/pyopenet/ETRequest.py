import contextlib
from io import BytesIO
import json
import threading
import time
import warnings

from logging import Logger, WARNING, ERROR, addLevelName
from pandas import read_csv
from requests import Response, post
from requests.exceptions import Timeout
from typing import Any, Hashable

STATUS_ALLOWED = [200]
TIMEOUT = 60 * 5

HELPFUL = 25
addLevelName(HELPFUL, "HELPFUL")

INTERRUPT_N = 0
INTERRUPT_LIMIT = 2
interruptlock = threading.Lock()

@contextlib.contextmanager
def interrupt_handler(): 
    global INTERRUPT_N, INTERRUPT_LIMIT
    with interruptlock:
        INTERRUPT_N = 0
    try:
        yield
    except KeyboardInterrupt:
        with interruptlock:
            INTERRUPT_N += 1
        if INTERRUPT_N >= INTERRUPT_LIMIT:
            raise
        else:
            print("KeyboardInterrupt detected. Press Ctrl+C again to quit.")
            raise KeyboardInterrupt # Workround so this handler doesn't need a larger scope and still letting the send() function handle the KeyboardInterrupt.

def format_json_response(response: Response) -> list[dict[str, Any]]:
    return json.loads(response.content.decode('utf-8'))

def format_csv_response(response: Response) -> list[dict[str | Hashable, Any]]:
    return read_csv(BytesIO(response.content)).to_dict(orient='records')

class Request:
    def __init__(
        self, 
        endpoint: str | None = None, 
        params: dict | None = {}, 
        key: str | None = None, 
        logger: Logger | None = None
    ) -> None:
        self.endpoint = endpoint
        self.params = params
        self.header = {"Authorization": key}
        self.logger = logger

        self._attempt: int = 1
        self.response: Response | None = None

    def _retry(self, attempts: int) -> None:
        while not self.success() and self._attempt <= attempts:
            self._log(WARNING, f"Reattempting request ({self._attempt}/{attempts})..")
            
            sleep_time = (2**self._attempt) % 10
            time.sleep(sleep_time)
            self._attempt += 1
            self.response = self.send()

    def _log(self, level: int, message: str, **kwargs) -> None:
        if not self.logger or not isinstance(self.logger, Logger):
            return

        self.logger.log(level, message, **kwargs)

    def send(
        self, max_retries: int = 3, ignore_fails: bool = False
    ) -> Response | None:
        if not self.endpoint:
            raise AttributeError("Request has no endpoint.")
        if not self.params:
            raise AttributeError("Request has no parameters.")
        if not self.header["Authorization"]:
            raise AttributeError("Request has no API key.")
        
        try:
            with interrupt_handler() as interrupted:
                self.response = post(
                    url=self.endpoint,
                    json=self.params,
                    headers=self.header,
                    timeout=TIMEOUT,
                )
                
            if interrupted or INTERRUPT_N >= INTERRUPT_LIMIT:
                return

            if not ignore_fails and not self.success():
                if self.response:
                    self._log(HELPFUL, f"Response[{self.response.status_code}]: {self.response.text}")
                raise ValueError("Request did not succeed with a 200 status code.")

        except KeyboardInterrupt:
            ignore_fails = True
            return

        except AttributeError as err:
            self._log(ERROR, f"Request failed.\n{err}")
            ignore_fails = True
            return

        except Timeout:
            # Automatically reattempts after timeout.
            self._log(ERROR, "Request timed out.")
            self._retry(max_retries)

        except Exception as err:
            self._log(ERROR, f"Request failed.\n{err}")
            self._retry(max_retries)

        finally:
            if not self.success() and not ignore_fails:
                req_feedback = ""
                if not self.response:
                    req_feedback = "Received no response from server. Please check your internet connection."
                else:
                    status = self.response.status_code
                    msg = self.response.text
                    req_feedback = f"Request failed with status code {status}. {msg}"

                self._log(ERROR, req_feedback)
                self._log(HELPFUL, str(self.params))

                will_reattempt = input(f"{req_feedback}\nReattempt request? (Y/n): ")

                if will_reattempt.lower() in ["y", ""]:
                    return self.send()

            return self.response

    def success(self) -> bool:
        # Returns true in the event that a response is returned and its status code is in STATUS_ALLOWED.
        try:
            return self.response.status_code in STATUS_ALLOWED  # type: ignore
        except Exception:
            return False

class ETRequest(Request):
    def __init__(self, request_endpoint=None, request_params=None, key=None) -> None:
        warnings.warn(
            "ETRequest is deprecated. Use Request instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(endpoint=request_endpoint, params=request_params, key=key)
        
    def send(self, logger=None, *args, **kwargs):
        super().send(*args, **kwargs)

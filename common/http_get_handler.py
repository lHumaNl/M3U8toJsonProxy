import base64
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler

import requests

from common.response_mock import ResponseMock
from common.settings import Settings


class HttpGetHandler(BaseHTTPRequestHandler):
    settings: Settings

    __UPDATE_M3U8_PATH = "/update_playlist"
    __UPDATE_EPG_PATH = "/update_epg"

    __OPTIONS_METHOD: str = "OPTIONS"
    __POST_METHOD: str = "POST"

    __METHOD_LIST = [__OPTIONS_METHOD, __POST_METHOD]

    def do_OPTIONS(self):
        self.send_response(204)

        self.send_header("Allow", ", ".join(self.__METHOD_LIST))
        self.end_headers()

    def do_POST(self):
        if self.path == self.__UPDATE_M3U8_PATH:
            self.send_response(200)

        if self.path == self.__UPDATE_EPG_PATH:
            self.send_response(200)


        if self.path not in self.settings.post_cached_response:
            self.settings.post_cached_response[self.path] = self.__get_null_cached_response(self.path)

        self.settings.post_cached_response[self.path] = self.__do_request_from_proxy_and_response_back(
            self.settings.post_cached_response[self.path],
            self.path,
            self.__POST_METHOD,
            dict(self.headers.items())
        )

    def __get_null_cached_response(self, path: str) -> ResponseMock:
        fail_message = f"Failed to get response from url: {self.settings.link_for_m3u8}{path}"
        status_code = 500

        null_cached_response = ResponseMock(fail_message, status_code)

        return null_cached_response

    def __do_request_from_proxy_and_response_back(self, cached_response: requests.Response, path: str, method: str,
                                                  headers: dict) -> requests.Response:
        if self.settings.append_parameter is not None:
            path = path + self.settings.append_parameter

        cached_response = self.__fill_cached_response(cached_response, method, self.settings.link_for_m3u8, path,
                                                      headers, self.settings.base64_key)

        self.send_response(cached_response.status_code)
        self.__add_headers_for_response()

        self.wfile.write(cached_response.text.encode())

        return cached_response

    def __add_headers_for_response(self):
        headers_dict = {
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store, no-cache",
            "Content-Type": "charset=utf-8",
            "Pragma": "no-cache",
            "Vary": "Accept-Encoding",
        }

        for header_key, header_value in headers_dict.items():
            self.send_header(header_key, header_value)

        self.end_headers()

    @staticmethod
    def __fill_cached_response(cached_response: requests.Response, method: str, host: str, path: str,
                               headers: dict, base64_key: str) -> requests.Response:
        if "Host" in headers:
            headers["Host"] = host.split("//")[1]

        if base64_key is not None:
            path = HttpGetHandler.__encode_to_base64_param_string(path, base64_key)

        temp_response = None
        try:
            if method == HttpGetHandler.__GET_METHOD:
                temp_response = requests.get(f"{host}{path}", headers=headers)
            elif method == HttpGetHandler.__POST_METHOD:
                temp_response = requests.post(f"{host}{path}", headers=headers)
        except Exception:
            pass

        if temp_response is not None and temp_response.status_code == 200:
            cached_response = temp_response

        return cached_response

    @staticmethod
    def __encode_to_base64_param_string(path: str, base64_key: str) -> str:
        parsed_params = urlparse(path).query.split("&")

        for param in parsed_params:
            param_key = param.split("=")[0]
            param_value = param.split("=")[1]

            if param_key == base64_key:
                base64_encoded_message = base64.b64encode(param_value.encode("ascii"))
                path = path.replace(param_value, base64_encoded_message.decode("ascii"))

                break

        return path

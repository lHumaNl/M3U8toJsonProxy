import cgi
import datetime
import json
import re
from http.server import BaseHTTPRequestHandler
from typing import Tuple, Dict, List

import pandas

from common.epg_parser import EPGParser
from common.m3u8_parser import M3U8Parser
from common.settings import Settings
from models.channel_data_model import ChannelData, EPGDfColumns
from models.param_names import ParamNames


class HttpGetHandler(BaseHTTPRequestHandler):
    settings: Settings

    __UPDATE_M3U8_PATH = "/update_playlist"
    __UPDATE_EPG_PATH = "/update_epg"

    __OPTIONS_METHOD: str = "OPTIONS"
    __GET_METHOD: str = "GET"
    __POST_METHOD: str = "POST"

    __METHOD_LIST = [__OPTIONS_METHOD, __GET_METHOD, __POST_METHOD]

    def do_OPTIONS(self):
        self.send_response(204)

        self.send_header("Allow", ", ".join(self.__METHOD_LIST))
        self.end_headers()

    def do_GET(self):
        status_code, body = self.__resolve_request_methods(self.__GET_METHOD)

        self.__send_response(status_code, body)

    def do_POST(self):
        status_code, body = self.__resolve_request_methods(self.__POST_METHOD)

        self.__send_response(status_code, body)

    def __send_response(self, status_code: int, body: str):
        self.send_response(status_code)
        self.__add_headers_to_response()

        self.wfile.write(body.encode())

    def __add_headers_to_response(self):
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

    def __update_playlist(self, status_code: int, body: str) -> Tuple[int, str]:
        try:
            M3U8Parser.get_playlist(self.settings)
        except Exception:
            status_code = 500

        if status_code == 200:
            try:
                EPGParser.format_epg_df_and_import_to_playlist(self.settings.epg_dataframe,
                                                               self.settings.get_channel_set(),
                                                               self.settings.m3u8_playlist)
            except Exception:
                status_code = 500
                body = self.__get_response_info_message(
                    f"Playlist has been updated, but import EPG to playlist has been failed!")

        if status_code == 200:
            body = self.__get_response_info_message("Playlist has been successfully updated!")

        return status_code, body

    def __update_epg(self, status_code: int, body: str) -> Tuple[int, str]:
        try:
            EPGParser.parse_epg_from_url(self.settings)
        except Exception:
            status_code = 500
            body = self.__get_response_info_message(
                f"Parsing EPG from {self.settings.link_for_epg} has been failed!")

        if status_code == 200:
            try:
                EPGParser.format_epg_df_and_import_to_playlist(self.settings.epg_dataframe,
                                                               self.settings.get_channel_set(),
                                                               self.settings.m3u8_playlist)
            except Exception:
                status_code = 500
                body = self.__get_response_info_message(f"Import EPG to playlist has been failed!")

        if status_code == 200:
            body = self.__get_response_info_message("EPG has been successfully updated!")

        return status_code, body

    @staticmethod
    def __get_response_info_message(response_info_message: str) -> str:
        message_dict = {
            "message": response_info_message
        }

        return json.dumps(message_dict, ensure_ascii=False, sort_keys=True, indent=4)

    @staticmethod
    def __format_json_response_for_groups(groups_dataframe: pandas.DataFrame, response_template: Dict) -> str:
        response_list: List[Dict] = []

        for group in groups_dataframe.to_dict('records'):
            group_dict = {
                key: group[value] if value in group.keys() else ''
                for key, value in response_template.items()
            }

            response_list.append(group_dict)

        return json.dumps(response_list, ensure_ascii=False, indent=4)

    @staticmethod
    def __format_json_response(playlist: Dict[str, ChannelData], response_template: Dict,
                               channel_key: str = None, is_time_from_now: bool = False) -> Tuple[int, str]:
        response_list: List[Dict] = []

        if channel_key is None:
            for channel_name, channel_data in playlist.items():
                channel_dict = {
                    key: channel_data.__dict__[value] if value in channel_data.__dict__.keys() else ''
                    for key, value in response_template.items()
                }

                response_list.append(channel_dict)
        else:
            if channel_key not in playlist and channel_key.isdigit():
                for channel in playlist.values():
                    if channel.id == int(channel_key):
                        channel_key = channel.name
                        break

            epg_dataframe: pandas.DataFrame = playlist[channel_key].epg_dataframe.copy()

            if is_time_from_now:
                time_now = int(datetime.datetime.now().timestamp())
                epg_dataframe = epg_dataframe[epg_dataframe[EPGDfColumns.STOP_COLUMN] > time_now]

            for epg in epg_dataframe.to_dict('records'):
                epg_dict = {
                    key: epg[value] if value in epg.keys() else ''
                    for key, value in response_template.items()
                }

                response_list.append(epg_dict)

        return 200, json.dumps(response_list, ensure_ascii=False, indent=4)

    def __parse_post_params(self) -> Dict:
        post_params_dict = {}

        try:
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            form_keys = form.keys()

            for key in form_keys:
                post_params_dict[key] = form.getvalue(key)
        except Exception:
            post_params_dict = {}

        return post_params_dict

    def __resolve_epg_and_m3u8_methods(self, method: str) -> Tuple[int, str]:
        if self.__search_endpoint_by_regex(self.path, self.settings.m3u8_regex_endpoint):
            status_code, body = self.__format_json_response(self.settings.m3u8_playlist,
                                                            self.settings.m3u8_response_template_channels)

            if self.settings.m3u8_response_template is not None:
                body = self.__replace_template_key_in_body(self.settings.m3u8_response_template,
                                                           ParamNames.TEMPLATE_CHANNELS, body)

                if self.settings.m3u8_response_template_group is not None:
                    groups = self.__format_json_response_for_groups(self.settings.m3u8_groups_dataframe,
                                                                    self.settings.m3u8_response_template_group)

                    body = body.replace(f'"{ParamNames.TEMPLATE_GROUP}"', groups)

        elif self.__search_endpoint_by_regex(self.path, self.settings.epg_regex_endpoint):
            if method == self.__POST_METHOD:
                if self.settings.epg_path_channel_regex is None:
                    post_params_dict = self.__parse_post_params()
                    channel_key = post_params_dict[self.settings.epg_post_param_channel_key]
                else:
                    channel_key = re.search(self.settings.epg_path_channel_regex, self.path).group(1)
            else:
                channel_key = re.search(self.settings.epg_path_channel_regex, self.path).group(1)

            status_code, body = self.__format_json_response(self.settings.m3u8_playlist,
                                                            self.settings.epg_response_template_program,
                                                            channel_key, self.settings.is_program_from_now)

            if self.settings.epg_response_template is not None:
                body = self.__replace_template_key_in_body(self.settings.epg_response_template,
                                                           ParamNames.TEMPLATE_PROGRAM, body)

        else:
            status_code = 404
            body = self.__get_response_info_message("Invalid endpoint/path!")

        return status_code, body

    def __resolve_request_methods(self, method: str) -> Tuple[int, str]:
        status_code: int = 200
        body: str = ''

        if self.__search_endpoint_by_regex(self.path, self.__UPDATE_M3U8_PATH):
            status_code, body = self.__update_playlist(status_code, body)

        elif self.__search_endpoint_by_regex(self.path, self.__UPDATE_EPG_PATH):
            status_code, body = self.__update_epg(status_code, body)

        elif self.__search_endpoint_by_regex(self.path, list(self.settings.mock_response_template.keys())):
            for regex in self.settings.mock_response_template.keys():
                if bool(re.search(regex, self.path)):
                    body = json.dumps(self.settings.mock_response_template[regex], ensure_ascii=False, indent=4)
                    break
        else:
            status_code, body = self.__resolve_epg_and_m3u8_methods(method)

        return status_code, body

    @staticmethod
    def __search_endpoint_by_regex(path: str, endpoint_regex) -> bool:
        if endpoint_regex is None:
            return False

        if type(endpoint_regex) == list:
            bool_result = False

            for regex in endpoint_regex:
                if bool(re.search(regex, path)):
                    bool_result = True

            return bool_result
        else:
            return bool(re.search(endpoint_regex, path))

    @staticmethod
    def __replace_template_key_in_body(response_template: Dict, dict_key: str, replace_str: str) -> str:
        return json.dumps(response_template, ensure_ascii=True, indent=4).replace(f'"{dict_key}"', replace_str)

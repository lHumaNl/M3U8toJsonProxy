import json
import logging
import os
import sys
import datetime
from typing import Dict, List, Any

import pandas
import pytz

from models.channel_data_model import ChannelData
from models.param_names import ParamNames


class Settings:
    util_port: int
    tz_zone: pytz

    link_for_m3u8: str
    link_for_epg: str

    m3u8_regex_endpoint: str
    epg_regex_endpoint: str

    update_time_for_m3u8: List[datetime.time]
    update_time_for_epg: List[datetime.time]

    m3u8_source_substring: Dict[str, str]

    is_program_from_now: bool

    epg_post_param_channel_key: str
    epg_path_channel_regex: str

    m3u8_response_template_channels: Dict
    m3u8_response_template_group: Dict
    m3u8_response_template: Dict

    epg_response_template_program: Dict
    epg_response_template: Dict

    mock_response_template: Dict

    m3u8_playlist: Dict[str, ChannelData]
    m3u8_groups_dataframe: pandas.DataFrame
    epg_dataframe: pandas.DataFrame

    def __init__(self, args_dict: Dict):
        m3u8_config_file_name = self.__get_value_from_dict(args_dict, ParamNames.M3U8_CONFIG)
        epg_config_file_name = self.__get_value_from_dict(args_dict, ParamNames.EPG_CONFIG)
        mock_config_file_name = self.__get_value_from_dict(args_dict, ParamNames.MOCK_CONFIG)

        m3u8_config: Dict = self.decode_json_file(os.path.join("config", m3u8_config_file_name))
        epg_config: Dict = self.decode_json_file(os.path.join("config", epg_config_file_name))

        self.util_port = self.__get_value_from_dict(args_dict, ParamNames.UTIL_PORT)
        tz_zone_name = self.__get_value_from_dict(args_dict, ParamNames.TZ_ZONE_NAME)
        self.tz_zone = pytz.timezone(tz_zone_name)

        self.link_for_m3u8 = self.__get_value_from_dict(m3u8_config, ParamNames.LINK)
        self.link_for_epg = self.__get_value_from_dict(epg_config, ParamNames.LINK, True)

        self.m3u8_regex_endpoint = self.__get_value_from_dict(m3u8_config, ParamNames.REGEX_ENDPOINT)
        self.epg_regex_endpoint = self.__get_value_from_dict(epg_config, ParamNames.REGEX_ENDPOINT)

        update_time_for_m3u8 = self.__get_value_from_dict(m3u8_config, ParamNames.UPDATE_SCHEDULE, True, [])
        self.update_time_for_m3u8 = self.__get_datetime_list_from_str_time_list(update_time_for_m3u8)

        update_time_for_epg = self.__get_value_from_dict(epg_config, ParamNames.UPDATE_SCHEDULE, True, [])
        self.update_time_for_epg = self.__get_datetime_list_from_str_time_list(update_time_for_epg)

        self.m3u8_source_substring = self.__get_value_from_dict(m3u8_config, ParamNames.REGEX_SOURCE_SUBSTRING, True)

        self.is_program_from_now = self.__get_value_from_dict(epg_config, ParamNames.IS_PROGRAM_FROM_NOW, True, False)

        self.epg_post_param_channel_key = self.__get_value_from_dict(epg_config, ParamNames.POST_PARAM_KEY, True)
        self.epg_path_channel_regex = self.__get_value_from_dict(epg_config, ParamNames.PATH_CHANNEL_REGEX, True)

        self.m3u8_response_template_channels = self.__get_value_from_dict(m3u8_config, ParamNames.TEMPLATE_CHANNELS)
        self.m3u8_response_template_group = self.__get_value_from_dict(m3u8_config, ParamNames.TEMPLATE_GROUP, True)
        self.m3u8_response_template = self.__get_value_from_dict(m3u8_config, ParamNames.TEMPLATE, True)

        self.epg_response_template_program = self.__get_value_from_dict(epg_config, ParamNames.TEMPLATE_PROGRAM)
        self.epg_response_template = self.__get_value_from_dict(epg_config, ParamNames.TEMPLATE, True)

        self.mock_response_template = self.decode_json_file(os.path.join("config", mock_config_file_name), True)

        self.m3u8_playlist = {}
        self.m3u8_groups_dataframe = pandas.DataFrame()
        self.epg_dataframe = pandas.DataFrame()

    def get_channel_set(self):
        m3u8_channel_name_set = {channel.name.lower() for channel in self.m3u8_playlist.values()}
        m3u8_tvg_id_set = {channel.tvg_id.lower() for channel in self.m3u8_playlist.values()}

        return {*m3u8_channel_name_set, *m3u8_tvg_id_set}

    @staticmethod
    def __get_datetime_list_from_str_time_list(str_time_list: List[str]) -> List[datetime.time]:
        datetime_list = []

        for time in str_time_list:
            datetime_list.append(datetime.datetime.strptime(time, '%H:%M').time())

        return datetime_list

    @staticmethod
    def __get_value_from_dict(config_dict: Dict, dict_key: str, pass_if_not_in_dict=False,
                              value_if_not_in_dict: Any = None) -> Any:
        if dict_key in config_dict:
            return config_dict[dict_key]
        else:
            if pass_if_not_in_dict:
                return value_if_not_in_dict
            else:
                logging.error(f'Key "{dict_key}" wasn\'t found in dict:'
                              f'{os.linesep + json.dumps(config_dict, ensure_ascii=False, indent=4)}')
                sys.exit(1)

    @staticmethod
    def decode_json_file(json_file: str, ignore_error: bool = False) -> Dict:
        if not os.path.exists(json_file):
            if ignore_error:
                return {}
            else:
                logging.error(f'"{os.path.basename(json_file)}" file not found')
                sys.exit(1)

        try:
            with open(json_file, "r", encoding="utf-8") as file:
                json_dict = json.load(file)
                file.close()

        except json.decoder.JSONDecodeError as json_decoder_error:
            logging.error(f'Failed to decode "{os.path.basename(json_file)}". Reason:{os.linesep}'
                          f'{f"{os.linesep}".join(arg for arg in json_decoder_error.args)}')
            sys.exit(1)
        except UnicodeDecodeError as unicode_decode_error:
            logging.error(unicode_decode_error.reason)
            sys.exit(1)

        return json_dict

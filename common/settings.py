import json
import logging
import os
import sys
from typing import Dict, List, Any

import pandas

from models.channel_data_model import ChannelData


class Settings:
    util_port: int
    tz_zone_name: str

    link_for_m3u8: str
    link_for_epg: str

    m3u8_regex_endpoint: str
    epg_regex_endpoint: str

    update_time_for_m3u8: List[str]
    update_time_for_epg: List[str]

    m3u8_response_template: Dict
    epg_response_template: Dict

    epg_channel_key: str
    epg_channel_regex: str

    m3u8_playlist: Dict[str, ChannelData]
    epg_dataframe: pandas.DataFrame

    def __init__(self, args_dict: Dict):
        self.util_port = args_dict["util_port"]

        self.tz_zone_name = args_dict["tz_zone_name"]

        m3u8_config: dict = self.decode_json_file(os.path.join("config", args_dict["m3u8_config"]))
        epg_config: dict = self.decode_json_file(os.path.join("config", args_dict["epg_config"]))
        mock_config: dict = self.decode_json_file(os.path.join("config", args_dict["mock_config"]), True)

        self.link_for_m3u8 = m3u8_config["link"]
        self.link_for_epg = epg_config["link"]

        self.m3u8_regex_endpoint = m3u8_config["regex_endpoint"]
        self.epg_regex_endpoint = epg_config["regex_endpoint"]

        if mock_config is not None:
            self.mock_regex_endpoint = mock_config["regex_endpoint"]

        self.update_time_for_m3u8 = m3u8_config["update_schedule"]
        self.update_time_for_epg = epg_config["update_schedule"]

        self.m3u8_response_template = m3u8_config["response_template"]
        self.epg_response_template = epg_config["response_template"]

        if mock_config is not None:
            self.mock_response_template = mock_config["response_template"]

        self.epg_channel_key = epg_config["channel_key"]
        self.epg_channel_regex = epg_config["channel_regex"]

        self.m3u8_playlist = {}
        self.epg_dataframe = pandas.DataFrame()

    def get_channel_set(self):
        m3u8_channel_name_set = {channel.name.lower() for channel in self.m3u8_playlist.values()}
        m3u8_tvg_id_set = {channel.tvg_id.lower() for channel in self.m3u8_playlist.values()}

        return {*m3u8_channel_name_set, *m3u8_tvg_id_set}

    @staticmethod
    def decode_json_file(json_file: str, ignore_error: bool = False) -> Dict | None:
        if not os.path.exists(json_file):
            if not ignore_error:
                logging.error(f'"{os.path.basename(json_file)}" file not found')
                sys.exit(1)
            else:
                return

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

import argparse
import json
import logging
import os
import sys
from typing import Dict

import pandas

from models.channel_data_model import ChannelData


class Settings:
    util_port: int
    link_for_m3u8: str
    link_for_epg: str
    update_time_for_m3u8: str
    update_time_for_epg: str
    tz_zone_name: str
    m3u8_playlist: dict[str, ChannelData]

    def __init__(self, args_dict):
        self.util_port = args_dict["util_port"]

        m3u8_config = self.decode_json_file(os.path.join("config", args_dict["m3u8_config"]))
        epg_config = self.decode_json_file(os.path.join("config", args_dict["epg_config"]))

        self.link_for_m3u8 = args_dict["link_for_m3u8"]
        self.link_for_epg = args_dict["link_for_epg"]

        self.update_time_for_m3u8 = args_dict["update_time_for_m3u8"]
        self.update_time_for_epg = args_dict["update_time_for_epg"]

        self.tz_zone_name = args_dict["tz_zone_name"]

        self.m3u8_playlist = {}
        self.epg_dataframe = pandas.DataFrame()

    def get_channel_set(self):
        m3u8_channel_name_set = {channel.name.lower() for channel in self.m3u8_playlist.values()}
        m3u8_tvg_id_set = {channel.tvg_id.lower() for channel in self.m3u8_playlist.values()}

        return {*m3u8_channel_name_set, *m3u8_tvg_id_set}

    @staticmethod
    def decode_json_file(json_file: str) -> Dict:
        if not os.path.exists(json_file):
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


def parse_console_args_and_get_settings() -> Settings:
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--util_port", type=int, default=os.environ.get("UTIL_PORT", default=9120))

    args_parser.add_argument("--m3u8_config", type=str,
                             default=os.environ.get("M3U8_CONFIG", default="m3u8_config.json"))

    args_parser.add_argument("--epg_config", type=str,
                             default=os.environ.get("EPG_CONFIG", default="epg_config.json"))

    args_parser.add_argument("--tz_zone_name", type=str, default=os.environ.get("TZ_ZONE_NAME",
                                                                                default="Europe/Moscow"))

    args_dict = args_parser.parse_args().__dict__

    settings = Settings(args_dict)

    return settings

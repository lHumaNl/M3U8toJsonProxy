import argparse
import logging
import os
import sys

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

        self.link_for_m3u8 = args_dict["link_for_m3u8"]
        self.link_for_epg = args_dict["link_for_epg"]

        self.update_time_for_m3u8 = args_dict["update_time_for_m3u8"]
        self.update_time_for_epg = args_dict["update_time_for_epg"]

        self.tz_zone_name = args_dict["tz_zone_name"]

        if self.link_for_m3u8 is None:
            logging.error("Link for m3u8 is NULL!")
            sys.exit(1)

        self.m3u8_playlist = {}
        self.epg_dataframe = pandas.DataFrame()

    def get_channel_set(self):
        m3u8_channel_name_set = {channel.name.lower() for channel in self.m3u8_playlist.values()}
        m3u8_tvg_id_set = {channel.tvg_id.lower() for channel in self.m3u8_playlist.values()}

        return {*m3u8_channel_name_set, *m3u8_tvg_id_set}


def parse_console_args_and_get_settings() -> Settings:
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--util_port", type=int, default=os.environ.get("UTIL_PORT", default=9120))

    args_parser.add_argument("--link_for_m3u8", type=str, default=os.environ.get("LINK_FOR_M3U8"))
    args_parser.add_argument("--link_for_epg", type=str, default=os.environ.get("LINK_FOR_EPG"))

    args_parser.add_argument("--update_time_for_m3u8", type=str, default=os.environ.get("UPDATE_TIME_FOR_M3U8"))

    args_parser.add_argument("--update_time_for_epg", type=str, default=os.environ.get("UPDATE_TIME_FOR_EPG",
                                                                                       default="00:00;12:00"))

    args_parser.add_argument("--tz_zone_name", type=str, default=os.environ.get("TZ_ZONE_NAME",
                                                                                default="Europe/Moscow"))

    args_dict = args_parser.parse_args().__dict__

    settings = Settings(args_dict)

    return settings

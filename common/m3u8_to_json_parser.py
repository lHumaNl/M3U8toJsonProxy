import logging
import re
from typing import List

import requests

from models.channel_data_model import ChannelData
from models.m3u8_tags import M3U8Tags, M3U8Regex


class M3U8Parser:
    @staticmethod
    def get_m3u8_dict(m3u8_link: str):
        try:
            m3u8_string = requests.get(m3u8_link).text
        except Exception:
            m3u8_string = None
            logging.error(f"Failed to get response from {m3u8_link}")

        if m3u8_string is not None:
            m3u8_list = M3U8Parser.__parse_m3u8_string(m3u8_string)

    @staticmethod
    def __parse_m3u8_string(m3u8_string: str) -> List:
        channel_list: list[ChannelData] = []

        channel_id = 1
        channel = ChannelData()
        for line in m3u8_string.split("\n"):

            if line.startswith("#"):

                if line.startswith(M3U8Tags.EXT_M3U):
                    epg_ulr = M3U8Parser.__parse_ext_m3u_tag(line)

                elif line.startswith(M3U8Tags.EXT_INF):
                    channel.id = channel_id
                    M3U8Parser.__parse_ext_inf_tag(line, channel)
                    channel_id += 1

                elif line.startswith(M3U8Tags.EXT_GRP):
                    pass

            else:
                channel.stream_url = line
                channel_list.append(channel)

                channel = ChannelData()

        return channel_list

    @staticmethod
    def __parse_ext_m3u_tag(line: str):
        if line.__contains__(M3U8Tags.URL_TVG):
            epg_ulr = re.search(M3U8Regex.URL_TVG_REGEX, line).group(1)

            return epg_ulr

    @staticmethod
    def __parse_ext_inf_tag(line: str, channel: ChannelData):
        if line.__contains__(M3U8Tags.TVG_ID):
            channel.tvg_id = re.search(M3U8Regex.TVG_ID_REGEX, line).group(1)

        if line.__contains__(M3U8Tags.GROUP_TITLE):
            channel.group = re.search(M3U8Regex.GROUP_TITLE_REGEX, line).group(1)

        if line.__contains__(M3U8Tags.TVG_LOGO):
            channel.logo_url = re.search(M3U8Regex.TVG_LOGO_REGEX, line).group(1)

        if line.__contains__(M3U8Tags.TIMESHIFT):
            channel.timeshift = re.search(M3U8Regex.TIMESHIFT_REGEX, line).group(1)

        channel.name = line.split(",")[1]



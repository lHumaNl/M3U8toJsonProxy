import logging
import re
from typing import List

import requests

from common.epg_to_json_parser import EPGParser
from models.channel_data_model import ChannelData
from models.m3u8_tags import M3U8Tags, M3U8Regex


class M3U8Parser:
    @staticmethod
    def get_playlist(m3u8_link: str) -> List:
        m3u8_playlist = None
        try:
            m3u8_text_response = requests.get(m3u8_link).content.decode('utf-8')
        except Exception:
            m3u8_text_response = None
            logging.error(f"Failed to get response from {m3u8_link}")

        if m3u8_text_response is not None:
            m3u8_playlist = M3U8Parser.__parse_m3u8_text_response(m3u8_text_response)

        return m3u8_playlist

    @staticmethod
    def __parse_m3u8_text_response(m3u8_text_response: str) -> list[ChannelData]:
        channel_list: list[ChannelData] = []
        epg_ulr = None

        channel_id = 1
        channel = ChannelData()
        for line in m3u8_text_response.split("\n"):

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

        if epg_ulr is not None:
            EPGParser.parse_epg_list(epg_ulr, channel_list)

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

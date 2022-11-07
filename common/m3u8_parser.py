import logging
import re

import requests

from common.settings import Settings
from models.channel_data_model import ChannelData
from models.m3u8_tags import M3U8Tags, M3U8Regex


class M3U8Parser:
    @staticmethod
    def get_playlist(settings: Settings):
        logging.info(f'Get m3u8 playlist from url: {settings.link_for_m3u8}')

        try:
            m3u8_text_response = requests.get(settings.link_for_m3u8).content.decode('utf-8')
        except Exception:
            m3u8_text_response = None
            logging.error(f"Failed to get response from {settings.link_for_m3u8}")

        if m3u8_text_response is not None:
            M3U8Parser.__parse_m3u8_text_response(m3u8_text_response, settings)

    @staticmethod
    def __parse_m3u8_text_response(m3u8_text_response: str, settings: Settings):
        epg_ulr = None

        logging.info('Start parsing m3u8 playlist')

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
                settings.m3u8_playlist[channel.name] = channel

                channel = ChannelData()

        logging.info('Parsing m3u8 playlist successfully completed!')

        if settings.link_for_epg is None and epg_ulr is not None:
            settings.link_for_epg = epg_ulr

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

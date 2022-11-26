import logging
import re

import pandas
import requests

from common.settings import Settings
from models.channel_data_model import ChannelData, ChannelGroupColumns
from models.m3u8_tags import M3U8Tags, M3U8Regex


class M3U8Parser:
    @staticmethod
    def get_playlist(settings: Settings):
        logging.info(f'Get m3u8 playlist from url: {settings.link_for_m3u8}')

        try:
            m3u8_text_response = requests.get(settings.link_for_m3u8).content.decode('utf-8')
        except requests.exceptions.ReadTimeout:
            m3u8_text_response = None
            logging.error(f'Read from "{settings.link_for_m3u8}" timeout!')
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
                source_link = line

                if settings.m3u8_source_substring is not None:
                    for regex, substring in settings.m3u8_source_substring.items():
                        source_link = re.sub(regex, substring, source_link)

                channel.stream_url = source_link
                settings.m3u8_playlist[channel.name] = channel

                channel = ChannelData()

        channel_group_list = [channel_data.group
                              for channel_data in settings.m3u8_playlist.values()]

        channel_group_count_dict = {
            channel_group: {
                ChannelGroupColumns.GROUP_COLUMN: channel_group,
                ChannelGroupColumns.COUNT_COLUMN: channel_group_list.count(channel_group)
            }
            for channel_group in channel_group_list}

        channel_group_count_dict[ChannelGroupColumns.ALL_CHANNEL_GROUP_NAME] = {
            ChannelGroupColumns.GROUP_COLUMN: ChannelGroupColumns.ALL_CHANNEL_GROUP_NAME,
            ChannelGroupColumns.COUNT_COLUMN: len(channel_group_list)
        }

        settings.m3u8_groups_dataframe = pandas.DataFrame(channel_group_count_dict.values())

        logging.info(f'Parsing m3u8 playlist successfully completed! Found {len(channel_group_list)} channels with '
                     f'{len(settings.m3u8_groups_dataframe[ChannelGroupColumns.GROUP_COLUMN].values) - 1} groups')

        if settings.link_for_epg is None and epg_ulr is not None:
            logging.info(f'Found url for EPG in playlist: {epg_ulr}')
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

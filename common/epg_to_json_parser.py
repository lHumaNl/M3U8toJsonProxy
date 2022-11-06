from datetime import datetime
import gzip
import logging
from typing import Dict

import pandas
import requests
import xmltodict

from models.channel_data_model import ChannelData, EPGDataframeColumns


class EPGParser:
    @staticmethod
    def parse_epg_list(epg_link: str, m3u8_playlist: list[ChannelData]):
        try:
            epg_xml_response = requests.get(epg_link).content
        except Exception:
            epg_xml_response = None
            logging.error(f"Failed to get response from {epg_link}")

        if epg_xml_response is not None:
            if epg_link.endswith(".gz"):
                epg_xml_response = gzip.decompress(epg_xml_response).decode('utf-8')

            EPGParser.__parse_epg_text_response(epg_xml_response, m3u8_playlist)

    @staticmethod
    def __parse_epg_text_response(epg_xml_response: str, m3u8_playlist: list[ChannelData]):
        m3u8_channel_name_set = {channel.name.lower() for channel in m3u8_playlist}
        m3u8_tvg_id_set = {channel.tvg_id.lower() for channel in m3u8_playlist}

        m3u8_channel_set = {*m3u8_channel_name_set, *m3u8_tvg_id_set}

        epg_dataframe = EPGParser.__get_epg_dataframe(epg_xml_response, m3u8_channel_set)

        for channel_in_playlist in m3u8_playlist:
            channel_name_set = {channel_in_playlist.name.lower(), channel_in_playlist.tvg_id.lower()}
            temp_dataframe = pandas.DataFrame()

            for channel_name in channel_name_set:
                if channel_name in epg_dataframe[EPGDataframeColumns.CHANNEL_COLUMN].unique():
                    channel_epg_df = epg_dataframe[epg_dataframe[EPGDataframeColumns.CHANNEL_COLUMN] == channel_name]

                    temp_dataframe = pandas.concat([temp_dataframe, channel_epg_df], ignore_index=True)

            if not temp_dataframe.empty:
                del temp_dataframe[EPGDataframeColumns.CHANNEL_COLUMN]
                channel_in_playlist.epg_dataframe = pandas.concat([channel_in_playlist.epg_dataframe, temp_dataframe],
                                                                  ignore_index=True)

    @staticmethod
    def __get_epg_dataframe(epg_xml_response: str, m3u8_channel_set: set):
        epg_dict = xmltodict.parse(epg_xml_response, encoding='utf-8')

        time_format = '%Y%m%d%H%M%S %z'
        formatted_epg_list = [
            {
                EPGDataframeColumns.CHANNEL_COLUMN: channel['display-name'].lower(),
                EPGDataframeColumns.START_COLUMN: int(datetime.strptime(program['@start'], time_format).timestamp()),
                EPGDataframeColumns.STOP_COLUMN: int(datetime.strptime(program['@stop'], time_format).timestamp()),
                EPGDataframeColumns.TITLE_COLUMN: program['title']['#text'] if '#text' in program['title'] else '',
                EPGDataframeColumns.DESCRIPTION_COLUMN: program['desc']['#text'] if '#text' in program['desc'] else ''
            }
            for program in epg_dict['tv']['programme']
            for channel in epg_dict['tv']['channel']

            if program['@channel'] in (channel['@id'],
                                       channel['display-name']) and (

                       channel['@id'].lower() in m3u8_channel_set or
                       channel['display-name'].lower() in m3u8_channel_set
               )
        ]

        return pandas.DataFrame(formatted_epg_list)

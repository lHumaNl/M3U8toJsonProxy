from datetime import datetime
import gzip
import logging

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
                epg_xml_response = gzip.decompress(epg_xml_response).decode()

            EPGParser.__parse_epg_text_response(epg_xml_response, m3u8_playlist)

    @staticmethod
    def __parse_epg_text_response(epg_xml_response: str, m3u8_playlist: list[ChannelData]):
        epg_dataframe = EPGParser.__get_epg_dataframe(epg_xml_response)

        for channel_in_playlist in m3u8_playlist:

            for channel_in_epg in epg_dataframe['tv']['programme']:

                if channel_in_epg['@channel'].lower() == channel_in_playlist.name.lower():

                    start = int(datetime.datetime.strptime(channel_in_epg['@start'], '%Y%m%d%H%M%S %z').timestamp())
                    stop = int(datetime.datetime.strptime(channel_in_epg['@stop'], '%Y%m%d%H%M%S %z').timestamp())

                    if '#text' in channel_in_epg['title']:
                        title = channel_in_epg['title']['#text']
                    else:
                        title = ''

                    if '#text' in channel_in_epg['desc']:
                        description = channel_in_epg['desc']['#text']
                    else:
                        description = ''

                    temp_dataframe = pandas.DataFrame(
                        {
                            EPGDataframeColumns.START_COLUMN: start,
                            EPGDataframeColumns.STOP_COLUMN: stop,
                            EPGDataframeColumns.TITLE_COLUMN: title,
                            EPGDataframeColumns.DESCRIPTION_COLUMN: description,
                        }, index=[0])

                    channel_in_playlist.epg_list = pandas.concat([channel_in_playlist.epg_list, temp_dataframe],
                                                                 ignore_index=True)

    @staticmethod
    def __get_epg_dataframe(epg_xml_response:str):
        epg_dict = xmltodict.parse(epg_xml_response)

        time_format = '%Y%m%d%H%M%S %z'
        formatted_epg_list = [
            {
                EPGDataframeColumns.CHANNEL_COLUMN: program['@channel'],
                EPGDataframeColumns.START_COLUMN: int(datetime.strptime(program['@start'], time_format).timestamp()),
                EPGDataframeColumns.STOP_COLUMN: int(datetime.strptime(program['@stop'], time_format).timestamp()),
                EPGDataframeColumns.TITLE_COLUMN: program['title']['#text'] if '#text' in program['title'] else '',
                EPGDataframeColumns.DESCRIPTION_COLUMN: program['desc']['#text'] if '#text' in program['desc'] else ''
            }
            for program in epg_dict['tv']['programme']
        ]

        return pandas.DataFrame(formatted_epg_list)

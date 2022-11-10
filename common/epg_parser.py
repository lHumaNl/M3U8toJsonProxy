from datetime import datetime
import gzip
import logging
from typing import Dict, List

import pandas
import requests
import xmltodict

from common.settings import Settings
from models.channel_data_model import EPGDfColumns, ChannelData


class EPGParser:
    @staticmethod
    def parse_epg_from_url(settings: Settings):
        logging.info(f'Get EPG from url: {settings.link_for_epg}')

        try:
            epg_xml_response = requests.get(settings.link_for_epg).content
        except Exception:
            epg_xml_response = None
            logging.error(f"Failed to get response from: {settings.link_for_epg}")

        if epg_xml_response is not None:
            if settings.link_for_epg.endswith(".gz"):
                epg_xml_response = gzip.decompress(epg_xml_response)

            settings.epg_dataframe = EPGParser.__get_epg_dataframe(epg_xml_response.decode('utf-8'))

    @staticmethod
    def format_epg_df_and_import_to_playlist(epg_dataframe: pandas.DataFrame, m3u8_channel_set: set,
                                             m3u8_playlist: Dict[str, ChannelData]):
        formatted_epg_dataframe = EPGParser.__removing_redundant_channels(epg_dataframe, m3u8_channel_set)
        EPGParser.__import_epg_in_playlist(m3u8_playlist, formatted_epg_dataframe)

    @staticmethod
    def __import_epg_in_playlist(m3u8_playlist: Dict[str, ChannelData], epg_dataframe: pandas.DataFrame):
        logging.info('Import EPG in playlist')

        for key, channel_in_playlist in m3u8_playlist.items():
            channel_in_playlist.epg_dataframe = pandas.DataFrame()

            channel_name_set = {channel_in_playlist.name.lower(), channel_in_playlist.tvg_id.lower()}
            temp_dataframe = pandas.DataFrame()

            for channel_name in channel_name_set:
                if channel_name in epg_dataframe[EPGDfColumns.CHANNEL_COLUMN].unique():
                    channel_epg_df = epg_dataframe[epg_dataframe[EPGDfColumns.CHANNEL_COLUMN] == channel_name]

                    temp_dataframe = pandas.concat([temp_dataframe, channel_epg_df], ignore_index=True)

            if not temp_dataframe.empty:
                del temp_dataframe[EPGDfColumns.CHANNEL_COLUMN]

                channel_in_playlist.epg_dataframe = EPGParser.__concat_dataframe(channel_in_playlist.epg_dataframe,
                                                                                 temp_dataframe)

        logging.info('Import EPG in playlist successfully completed!')

    @staticmethod
    def __get_epg_dataframe(epg_xml_response: str):
        logging.info('Start parsing EPG')

        epg_dict = xmltodict.parse(epg_xml_response, encoding='utf-8')

        tv_key = 'tv'
        channel_name = 'channel_name'
        tvg_id = 'tvg_id'

        channel_name_dict = EPGParser.__get_channel_name_dict(epg_dict, tv_key, channel_name, tvg_id)
        formatted_epg_list = EPGParser.__get_formatted_epg_list(epg_dict, channel_name_dict, channel_name, tv_key,
                                                                tvg_id)

        logging.info('Parsing EPG successfully completed!')

        return pandas.DataFrame(formatted_epg_list)

    @staticmethod
    def __removing_redundant_channels(epg_dataframe: pandas.DataFrame, m3u8_channel_set: set) -> pandas.DataFrame:
        logging.info('Start removing redundant channels from EPG')

        channel_epg_dataframe = epg_dataframe[
            epg_dataframe[EPGDfColumns.CHANNEL_COLUMN].isin(m3u8_channel_set)]

        tvg_epg_dataframe = epg_dataframe[
            epg_dataframe[EPGDfColumns.TVG_COLUMN].isin(m3u8_channel_set)]

        if not channel_epg_dataframe.empty:
            del channel_epg_dataframe[EPGDfColumns.TVG_COLUMN]

        if not tvg_epg_dataframe.empty:
            del tvg_epg_dataframe[EPGDfColumns.CHANNEL_COLUMN]
            tvg_epg_dataframe = tvg_epg_dataframe.rename(columns={EPGDfColumns.TVG_COLUMN: EPGDfColumns.CHANNEL_COLUMN})

        logging.info('Removing redundant channels from EPG successfully completed!')

        return EPGParser.__concat_dataframe(channel_epg_dataframe, tvg_epg_dataframe)

    @staticmethod
    def __concat_dataframe(source_df: pandas.DataFrame, append_df: pandas.DataFrame) -> pandas.DataFrame:
        return pandas.concat([source_df, append_df], ignore_index=True).drop_duplicates().reset_index(drop=True)

    @staticmethod
    def __get_channel_name_dict(epg_dict: Dict, tv_key: str, channel_name: str, tvg_id: str) -> Dict:
        id_key = '@id'
        display_name_key = 'display-name'

        channel_name_dict = {}
        for channel in epg_dict[tv_key]['channel']:
            channel_name_dict[channel[id_key].lower()] = {
                channel_name: channel[display_name_key].lower(),
                tvg_id: channel[id_key].lower(),
            }

            channel_name_dict[channel[display_name_key].lower()] = {
                channel_name: channel[display_name_key].lower(),
                tvg_id: channel[id_key].lower(),
            }

        return channel_name_dict

    @staticmethod
    def __get_formatted_epg_list(epg_dict: Dict, channel_name_dict: Dict, channel_name: str, tv_key: str,
                                 tvg_id: str) -> List:
        channel_key = '@channel'
        start_key = '@start'
        stop_key = '@stop'
        text_key = '#text'

        title_key = 'title'
        desc_key = 'desc'

        time_format = '%Y%m%d%H%M%S %z'
        formatted_epg_list = [
            {
                EPGDfColumns.CHANNEL_COLUMN: channel_name_dict[program[channel_key].lower()][channel_name],
                EPGDfColumns.TVG_COLUMN: channel_name_dict[program[channel_key].lower()][tvg_id],
                EPGDfColumns.START_COLUMN: int(datetime.strptime(program[start_key], time_format).timestamp()),
                EPGDfColumns.STOP_COLUMN: int(datetime.strptime(program[stop_key], time_format).timestamp()),
                EPGDfColumns.TITLE_COLUMN: program[title_key][text_key] if text_key in program[title_key] else '',
                EPGDfColumns.DESCRIPTION_COLUMN: program[desc_key][text_key] if text_key in program[desc_key] else ''
            }
            for program in epg_dict[tv_key]['programme']
        ]

        return formatted_epg_list

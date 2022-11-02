import gzip
import logging
from typing import List

import requests
import xmltodict


class EPGParser:
    @staticmethod
    def get_epg_list(epg_link: str) -> List:
        epg_list = None

        try:
            epg_xml_response = requests.get(epg_link).content
        except Exception:
            epg_xml_response = None
            logging.error(f"Failed to get response from {epg_link}")

        if epg_xml_response is not None:
            if epg_link.endswith(".gz"):
                epg_xml_response = gzip.decompress(epg_xml_response).decode()

            epg_list = EPGParser.__parse_epg_text_response(epg_xml_response)

        return epg_list

    @staticmethod
    def __parse_epg_text_response(epg_xml_response: str) -> List:
        epg_dict = xmltodict.parse(epg_xml_response)


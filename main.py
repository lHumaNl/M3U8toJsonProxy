import argparse
import os
from http.server import HTTPServer
from typing import Dict

import urllib3

from common.epg_parser import EPGParser
from common.http_get_handler import HttpGetHandler
from common.m3u8_parser import M3U8Parser
from common.settings import Settings
from models.logger_model import LoggerModel


def parse_console_args_and_get_settings() -> Dict:
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--util_port", type=int, default=os.environ.get("UTIL_PORT", default=9120))

    args_parser.add_argument("--m3u8_config", type=str,
                             default=os.environ.get("M3U8_CONFIG", default="m3u8_config.json"))

    args_parser.add_argument("--epg_config", type=str,
                             default=os.environ.get("EPG_CONFIG", default="epg_config.json"))

    args_parser.add_argument("--mock_config", type=str,
                             default=os.environ.get("MOCK_CONFIG", default="mock_config.json"))

    args_parser.add_argument("--tz_zone_name", type=str, default=os.environ.get("TZ_ZONE_NAME",
                                                                                default="Europe/Moscow"))

    args_dict = args_parser.parse_args().__dict__

    return args_dict


def main():
    LoggerModel.init_logger()
    urllib3.disable_warnings()

    args_dict = parse_console_args_and_get_settings()
    settings = Settings(args_dict)

    M3U8Parser.get_playlist(settings)

    if settings.link_for_epg is not None:
        EPGParser.parse_epg_from_url(settings)
        EPGParser.format_epg_df_and_import_to_playlist(settings.epg_dataframe, settings.get_channel_set(),
                                                       settings.m3u8_playlist)

    # threading.Thread(target=M3U8Parser.get_playlist, daemon=True).start()

    http_get_handler = HttpGetHandler
    http_get_handler.settings = settings

    web_server = HTTPServer(("", settings.util_port), http_get_handler)

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        web_server.server_close()


if __name__ == '__main__':
    main()

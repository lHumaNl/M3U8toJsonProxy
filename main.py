import threading
from http.server import HTTPServer

import urllib3

from common.epg_parser import EPGParser
from common.http_get_handler import HttpGetHandler
from common.m3u8_parser import M3U8Parser
from common.settings import parse_console_args_and_get_settings
from models.logger_model import LoggerModel


def main():
    LoggerModel.init_logger()
    urllib3.disable_warnings()

    settings = parse_console_args_and_get_settings()

    M3U8Parser.get_playlist(settings)

    if settings.link_for_epg is not None:
        EPGParser.parse_epg_from_url(settings)

    #threading.Thread(target=M3U8Parser.get_playlist, daemon=True).start()

    http_get_handler = HttpGetHandler
    http_get_handler.settings = settings

    web_server = HTTPServer(("", settings.util_port), http_get_handler)

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        web_server.server_close()


if __name__ == '__main__':
    main()

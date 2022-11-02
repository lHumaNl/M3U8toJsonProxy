import threading
from http.server import HTTPServer

from common.epg_to_json_parser import EPGParser
from common.http_get_handler import HttpGetHandler
from common.m3u8_to_json_parser import M3U8Parser
from common.settings import parse_console_args_and_get_settings


def main():
    settings = parse_console_args_and_get_settings()

    M3U8Parser.get_playlist(settings.link_for_m3u8)

    threading.Thread(target=M3U8Parser.get_playlist, daemon=True).start()
    threading.Thread(target=EPGParser.parse_epg_to_dict, daemon=True).start()

    http_get_handler = HttpGetHandler
    http_get_handler.settings = settings

    web_server = HTTPServer(("", settings.util_port), http_get_handler)

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        web_server.server_close()


if __name__ == '__main__':
    main()

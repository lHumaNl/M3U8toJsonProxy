class M3U8Tags:
    EXT_M3U = '#EXTM3U'
    EXT_INF = '#EXTINF'
    EXT_GRP = '#EXTGRP'

    URL_TVG = "url-tvg="
    TVG_LOGO = "tvg-logo="
    TVG_ID = "tvg-id="
    TIMESHIFT = "timeshift="
    GROUP_TITLE = "group-title="


class M3U8Regex:
    URL_TVG_REGEX = 'url-tvg="(.*?)"'
    TVG_LOGO_REGEX = 'tvg-logo="(.*?)"'
    TVG_ID_REGEX = 'tvg-id="(.*?)"'
    TIMESHIFT_REGEX = 'timeshift="(.*?)"'
    GROUP_TITLE_REGEX = 'group-title="(.*?)"'

import pandas


class EPGDataframeColumns:
    CHANNEL_COLUMN = 'channel'
    START_COLUMN = 'start'
    STOP_COLUMN = 'stop'
    TITLE_COLUMN = 'title'
    DESCRIPTION_COLUMN = 'description'


class ChannelData:
    id: int
    tvg_id: str
    name: str
    group: str
    logo_url: str
    timeshift: int
    stream_url: str
    epg_dataframe: pandas.DataFrame

    # noinspection PyTypeChecker
    def __init__(self):
        self.id = None
        self.tvg_id = None
        self.name = None
        self.group = None
        self.logo_url = None
        self.timeshift = None
        self.stream_url = None
        self.epg_dataframe = pandas.DataFrame()

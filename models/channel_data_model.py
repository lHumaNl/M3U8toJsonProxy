class ChannelData:
    id: int
    tvg_id: str
    name: str
    group: str
    logo_url: str
    timeshift: int
    stream_url: str

    # noinspection PyTypeChecker
    def __init__(self):
        self.id = None
        self.tvg_id = None
        self.name = None
        self.group = None
        self.logo_url = None
        self.timeshift = None
        self.stream_url = None

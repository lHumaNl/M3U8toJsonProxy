from requests import Response


class ResponseMock(Response):
    def __init__(self, text: str, status_code: int):
        super().__init__()
        self.text = text
        self.status_code = status_code

    def text(self) -> str:
        return self.text

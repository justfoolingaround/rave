import re
from collections import deque, namedtuple
from hashlib import md5
from typing import Union
from urllib.parse import quote

import httpx

response_cache = namedtuple(
    "response_cache", ["cbs", "response", "xai"], defaults=[None, None, None]
)

COOKIE_HOLDER_REGEX = re.compile(r'<script async src="(/extras/.+?)">')


class CleverBotClient:
    def __init__(
        self, session: "Union[httpx.AsyncClient, httpx.Client]", service_url: str
    ):
        self.history = deque(maxlen=6)
        self.session = session

        self.response_cache = response_cache()
        self.service_url = service_url

    @staticmethod
    def quote(message: "str"):
        return quote(message).replace("%u", "|")

    @staticmethod
    def create_payload(message: "str", *, history=None):

        payload = "stimulus={}".format(CleverBotClient.quote(message))

        if history is not None:
            payload += "&{}".format(
                "&".join(
                    "vText{}={}".format(_, CleverBotClient.quote(ctx_item))
                    for _, ctx_item in enumerate(list(history), 2)
                )
            )

        payload += "&cb_settings_language=en&cb_settings_scripting=no&islearning=1&icognoid=wsf&icognocheck="
        return payload + md5(payload[7:33].encode()).hexdigest()

    def construct_parameters(
        self, message: "str", cbs=None, xai=None, last_response=None
    ):
        params = {
            "uc": "UseOfficialCleverbotAPI",
        }

        if cbs is not None:
            params.update(
                {
                    "out": self.quote(last_response),
                    "in": self.quote(message),
                    "cbsid": cbs,
                    "xai": xai,
                }
            )

        return params

    async def acommunicate(self, message: "str"):
        return self.register(
            message,
            await self.session.post(
                self.service_url,
                params=self.construct_parameters(message, *self.response_cache),
                data=self.create_payload(message, history=self.history),
            ),
        )

    def communicate(self, message: "str"):
        return self.register(
            message,
            self.session.post(
                self.service_url,
                params=self.construct_parameters(message, *self.response_cache),
                data=self.create_payload(message, history=self.history),
            ),
        )

    def register(self, message: "str", http_response: "httpx.Response"):

        if http_response.status_code != 200:
            return None

        lines = http_response.text.splitlines()
        response, cbs = lines[:2]

        xai = "{},{}".format(cbs[:3], lines[2])

        self.response_cache = response_cache(cbs=cbs, response=response, xai=xai)
        self.history.extendleft((message, response))
        return response

    @classmethod
    async def ainitialise(
        cls,
        session: "httpx.AsyncClient",
        *,
        url="https://www.cleverbot.com/",
        service_endpoint="webservicemin"
    ):
        cookie_holder = COOKIE_HOLDER_REGEX.search((await session.get(url)).text)

        if cookie_holder is not None:
            await session.get(
                url + cookie_holder.group(1), headers={"Range": "bytes=0-0"}
            )

        return cls(session, url + service_endpoint)

    @classmethod
    def initialise(
        cls,
        session: "httpx.Client",
        *,
        url="https://www.cleverbot.com/",
        service_endpoint="webservicemin"
    ):

        cookie_holder = COOKIE_HOLDER_REGEX.search(session.get(url).text)

        if cookie_holder is not None:
            session.get(url + cookie_holder.group(1), headers={"Range": "bytes=0-0"})

        return cls(session, url + service_endpoint)

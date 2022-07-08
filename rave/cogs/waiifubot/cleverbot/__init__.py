import datetime
import random
import time
from hashlib import md5
from urllib.parse import quote

import requests


def quote_data(data: dict):
    return "&".join(
        f"{key}={quote(value).replace('|', '%u')}" for key, value in data.items()
    )


class CleverBotWebService:
    def __init__(self, url: str):

        self.session = requests.session()

        self.url = url

        self.webservice = url + "webservicemin"
        self.history = list()

        self.session_id = None
        self.xai = None

    def set_xvis_cookie(self):

        self.session.get(
            self.url
            + f"extras/conversation-social-min.js?{format(datetime.datetime.now(), '%Y%m%d')}"
        )

        self.session.cookies.update({"_cbsid": "-1"})

    def talk(self, message: "str | None" = None):

        if "XVIS" not in self.session.cookies:
            self.set_xvis_cookie()

        payload = {}

        if message is None:
            payload.update({"stimulus": "{pass}", "Sub": "Pass"})
        else:
            payload.update(
                {
                    "stimulus": message,
                }
            )

        for count, previous_message in enumerate(self.history[::-1], 2):
            payload.update({f"vText{count}": previous_message})

        payload.update(
            {
                "cb_setting_language": "en",
                "cb_settings_scripting": "no",
            }
        )

        if self.session_id is not None:
            payload.update({"sessionid": self.session_id})

        payload.update(
            {
                "islearning": "1",
                "icognoid": "wsf",
            }
        )

        parsed = quote_data(payload) + "&icognocheck="
        parsed += md5(parsed[7:33].encode()).hexdigest()

        if self.session_id is None:

            response = self.session.post(
                self.webservice,
                params={"uc": "UseOfficialCleverbotAPI", "ncf": "V2"},
                data=parsed,
            )

            bot_message, self.session_id, self.xai, *_ = response.text.split("\r")

            self.session.cookies.update(
                {
                    "CBALT": f"1~{bot_message}",
                    "CBSID": self.session_id,
                }
            )

            self.session.get(
                self.webservice,
                params={
                    "uc": "UseOfficialCleverbotAPI",
                    "ncf": "V2",
                    "in": payload.get("stimulus"),
                    "bot": "c",
                    "cbsid": self.session_id,
                    "xai": self.session.cookies.get("XAI"),
                    "ns": len(self.history) + 1,
                    "flag": "P",
                    "mode": "1",
                    "alt": "0",
                    "sou": "website",
                },
            )

        else:
            self.session.cookies.update(
                {
                    "CBALT": f"1~{self.history[-1]}",
                    "CBSTATE": quote(
                        f"&&0&&0{len(self.history)}&" + "&".join(self.history)
                    ),
                }
            )

            is_response_ok = False

            while not is_response_ok:
                response = self.session.post(
                    self.webservice,
                    params={
                        "uc": "UseOfficialCleverbotAPI",
                        "ncf": "V2",
                        "out": self.history[-1],
                        "in": payload.get("stimulus"),
                        "bot": "c",
                        "cbsid": self.session_id,
                        "xai": f"{self.session.cookies.get('XAI')},{self.xai}",
                        "ns": len(self.history) + 1,
                        "dl": "en",
                        "mode": "1",
                        "alt": "0",
                        "sou": "website",
                    },
                    data=parsed,
                )
                is_response_ok = response.status_code == 200

                if is_response_ok:
                    time.sleep(1.5)

            bot_message, self.session_id, self.xai, *_ = response.text.split("\r")

        self.history.extend((payload.get("stimulus"), bot_message))

        return bot_message


SERVICES = {
    "cleverbot-official": ("https://www.cleverbot.com/"),
    "boibot": ("https://www.boibot.com/"),
    "pewdiebot": ("https://www.pewdiebot.com/"),
    "eviebot": ("https://www.eviebot.com/"),
    "thoughtscreen": ("https://www.thoughtscreen.com/"),
}


def get_unique_client():
    return CleverBotWebService(random.choice(list(SERVICES.values())))

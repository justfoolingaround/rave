import time
from collections import defaultdict

import regex
import yarl
from discord.utils import escape_markdown

GITHUB_REPO_REGEX = regex.compile(
    r"(?:https?://)(?:.+?\.)*github\.com/(.+?/.+?)/blob/([^?#&]+)(?:#L(\d+)(?:-L(\d+))?)?"
)

TRUNCATED = """
... (Truncated; {} more characters)
"""

TEMPLATE = """
Viewing [{file}]({original_url}) at [{repository}](https://github.com/{repository}){index_string}:
```{extension}
{code}
```
[Source]({original_url}), [Raw]({raw_url})
"""


def truncate(string, limit):
    if len(string) > limit:
        _, sep_index = max(
            ((_, string[: limit - 125].rfind(_)) for _ in ["\n", " "]),
            key=lambda x: x[1],
        )
        return string[:sep_index].replace("```", "\\```") + TRUNCATED.format(
            len(string) - sep_index
        )
    return string


def get_index(start_line: "None | str", end_line: "None | str"):

    if start_line is None:
        start_line = 0
    else:
        start_line = int(start_line)

    if end_line is not None:
        end_line = int(end_line)

        if start_line > end_line:
            start_line, end_line = end_line, start_line

    if not start_line:
        return "", 0, None

    if end_line is None:
        return " **L{}**".format(start_line), start_line, end_line

    return " **L{}-{}**".format(start_line, end_line), start_line, end_line


async def generate_codelines(
    session, github_uri_match, *, size_limit=2500, download_limit=2 * 1024**2
):

    url = yarl.URL(github_uri_match.group(0)).with_query({"raw": "true"})
    repository, _, start_line, end_line = github_uri_match.groups()

    request_head = await session.head(url.human_repr())

    if (request_head.status_code > 399) or int(
        request_head.headers.get("content-length", 0)
    ) > download_limit:
        return

    resource = (await session.get(url.human_repr())).text.splitlines()

    index_string, from_, to_ = get_index(start_line, end_line)

    if to_ is None:
        code = resource[from_]
    else:
        code = "\n".join(resource[from_ - 1 : to_])

    _, _, ext = url.name.rpartition(".")

    return TEMPLATE.format(
        file=escape_markdown(url.name),
        original_url=github_uri_match.group(0),
        repository=repository,
        index_string=index_string,
        extension=ext or "",
        code=truncate(code, size_limit).rstrip(),
        raw_url=url.human_repr(),
    )


class Ratelimit:
    def __init__(self, exemptions=list(), invert_exemptions=False, *, per=2):
        """
        A basic but powerful ratelimit client to kill spammers.
        """
        self.storage = defaultdict(int)

        self.exemptions = exemptions
        self.invert = invert_exemptions

        self.per = per

    async def perform(self, unique_identifier, task=None):

        if unique_identifier in self.exemptions:
            if not self.invert:
                return False, ((await task()) if task else None)
        else:
            if self.invert:
                return False, ((await task()) if task else None)

        rate_expiration = self.storage[unique_identifier]

        if rate_expiration < time.time():
            self.storage[unique_identifier] = time.time() + self.per
            return False, ((await task()) if task else None)

        return True, None

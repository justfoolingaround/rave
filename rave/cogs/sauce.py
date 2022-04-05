from functools import reduce
from typing import Optional, Union

import anitopy
import discord
import httpx
import regex
from discord.ext import commands

from .. import commands as custom_commands

TRACEMOE_API = "https://api.trace.moe/search?cutBorders"

BLACKBOX_API = "https://www.blackboxapp.co/getsingleimage"

ANILIST_GQL = "https://graphql.anilist.co/"
ANILIST_REGEX = regex.compile(r"(?:https?://)?anilist\.co/anime/(?P<content_id>\d+)")

GQL_COMMAND = """\
query ($ids: [Int]) {
    Page(page: 1, perPage: 50) {
        media(id_in: $ids, type: ANIME) {
            id
            title {
                userPreferred 
                native
                romaji
                english
                }
            status(version:2)
            episodes
        }
    }
}"""


def to_timestamp(seconds):
    minute, second = divmod(int(seconds), 60)
    hour, minute = divmod(minute, 60)

    if hour:
        return "{:02d}:{:02d}:{:02d}".format(hour, minute, second)

    return "{:02d}:{:02d}".format(minute, second)


async def get_sauce(client: "httpx.AsyncClient", url: str):
    sauce = (await client.post(TRACEMOE_API, params={"url": url})).json()

    error = sauce.get("error")

    if error:
        return False, [error]

    return True, sauce.get("result", [])


async def gather_anilist(client: "httpx.AsyncClient", content_ids):
    return {
        content.get("id"): content
        for content in (
            await client.post(
                ANILIST_GQL,
                json={"query": GQL_COMMAND, "variables": {"ids": list(content_ids)}},
            )
        )
        .json()
        .get("data", {})
        .get("Page")
        .get("media", [])
    }


def get_string(url, status, result, anilists):

    if not status:
        return "Error {!r} occured for [content.]({})".format(result, url)

    anilist = result.get("anilist")

    if anilist is None:
        anitopy_parsed = anitopy.parse(result.get("filename"))
        content_name = anitopy_parsed.get("anime_title")

        season = anitopy_parsed.get("anime_season")
        if season:
            season_prefix = anitopy_parsed.get("anime_season_prefix")
            if season_prefix:
                season = season_prefix + season
            content_name = " ".join((content_name, season))

        episode = anitopy_parsed.get("episode_number")
        if episode:
            episode_prefix = anitopy_parsed.get("episode_number_prefix")
            if episode_prefix:
                episode = episode_prefix + episode
            content_name = " ".join((content_name, episode))

        content_name = "[{}]({})".format(content_name, url)

    else:
        anime = anilists.get(anilist, {})

        titles = anime.get("title", {})
        content_name = (
            titles.get("userPreferred")
            or titles.get("romaji")
            or titles.get("english")
            or titles.get("native")
        )
        content_status = anime.get("status")

        episode = result.get("episode")

        if episode is not None:
            if content_status == "FINISHED":
                end_episode = anime.get("episodes")
                episode = "**{}**/{}".format(episode, end_episode)
            else:
                episode = "**{}**".format(episode)

            content_name = " ".join((content_name, episode))

        content_name = "[{}](https://anilist.co/anime/{})".format(content_name, anilist)

    fragments = ["{:.01f}% @ {}".format(result.get("similarity") * 100, content_name)]

    from_ = result.get("from")

    if from_:
        stamp = to_timestamp(from_)
        to = result.get("to")
        if to:
            stamp = "{}-{}".format(stamp, to_timestamp(to))

        fragments.append(stamp)

    video = result.get("video")

    if video:
        fragments.append("[Clip]({})".format(video))

    image = result.get("image")

    if image:
        fragments.append("[Screenshot]({})".format(image))

    return " | ".join(fragments)


class SauceCog(custom_commands.AdjustibleCog):
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=300.0)

    @commands.command()
    @commands.is_owner()
    async def sauce(self, ctx: custom_commands.Context, url: Optional[str] = None):

        content = []

        if url is not None:
            content.append((url, await get_sauce(self.client, url)))

        for attachment in ctx.message.attachments:
            content.append(
                (attachment.url, await get_sauce(self.client, attachment.url))
            )

        anilists = await gather_anilist(
            self.client,
            reduce(
                list.__add__,
                [
                    [
                        result.get("anilist")
                        for result in results
                        if result.get("anilist")
                    ]
                    for _, (status, results) in content
                    if status
                ],
                [],
            ),
        )

        if len(content) == 1:
            content_url, (status, results) = content[0]

            return await self.send_smartly(
                ctx,
                "\n".join(
                    get_string(content_url, status, result, anilists)
                    for result in results
                ),
                footer="Scavenging the sauce for you, {}",
                title="Sauce",
            )

        return await self.send_smartly(
            ctx,
            "\n".join(
                "\n".join(
                    "`{}.{}` {}".format(
                        count,
                        internal_count,
                        get_string(content_url, status, result, anilists),
                    )
                    for internal_count, result in enumerate(results, 1)
                )
                for count, (content_url, (status, results)) in enumerate(content, 1)
            ),
        )

    @commands.command()
    @commands.is_owner()
    async def wtf(
        self,
        ctx: custom_commands.Context,
        message_or_url: Optional[Union[discord.Message, str]],
    ):

        searching = list(map(lambda a: a.url, ctx.message.attachments))

        if message_or_url is not None:
            if isinstance(message_or_url, discord.Message):
                searching.extend(map(lambda a: a.url, message_or_url.attachments))
            else:
                searching.append(message_or_url)

        if not searching:
            return await self.send_smartly(
                ctx,
                "Could not find any attachment in the message.",
                color=discord.Colour.red(),
            )

        for url in searching:

            response = await self.client.get(url)
            api_response = (
                await self.client.post(
                    BLACKBOX_API,
                    files={
                        "photo": (
                            "kr",
                            response.read(),
                            response.headers.get("content-disposition", "image/png"),
                        )
                    },
                )
            ).json()
            if api_response != "Error":
                await self.send_smartly(
                    ctx,
                    "```\n{}```".format(
                        (api_response.get("text", "").replace("```", "\\```"))
                    ),
                    color=discord.Colour.green(),
                    thumbnail={"url": url},
                )


def setup(bot):
    bot.add_cog(SauceCog())

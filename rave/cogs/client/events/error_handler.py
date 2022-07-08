import traceback

from discord.errors import *
from discord.ext.commands.errors import *


def expand_exception_args(error):
    return traceback.format_exc()


def check_failure_error_handler(error):
    if isinstance(error, CheckAnyFailure):
        return "Unauthorized due to check failure on multiple occasions:\n{}".format(
            ", ".join(
                "- {}".format(check_failure_error_handler(err)) for err in error.errors
            )
        )

    if isinstance(error, PrivateMessageOnly):
        return "This command can only be called in private messages or DMs."

    if isinstance(error, NoPrivateMessage):
        return "This command cannot be called in private messages or DMs."

    if isinstance(error, NotOwner):
        return "Unauthorized; only the bot owners can use this command."

    if isinstance(error, MissingRole):
        return "This command can only be called if the user has the role {!r}.".format(
            error.missing_role
        )

    if isinstance(error, BotMissingRole):
        return "This command can only be called if the bot has the role {!r}.".format(
            error.missing_role
        )

    if isinstance(error, MissingAnyRole):
        *r, _ = ["{!r}".format(role) for role in error.missing_roles]
        return "This command can only be called if the user has at least one of the roles: {}.".format(
            "{}, or ".format(", ".join(r), _)
        )

    if isinstance(error, BotMissingAnyRole):
        *r, _ = ["{!r}".format(role) for role in error.missing_roles]
        return "This command can only be called if the user has at least one of the roles: {}.".format(
            "{}, or ".format(", ".join(r), _)
        )

    if isinstance(error, NSFWChannelRequired):
        return "This command can only be called if the channel is marked as NSFW."

    if isinstance(error, MissingPermissions):
        *p, _ = [perm.replace("_", " ").title() for perm in error.missing_perms]
        return "This command can only be called if the user has the permissions: {}.".format(
            "{}, or ".format(", ".join(p), _)
        )

    if isinstance(error, BotMissingPermissions):
        *p, _ = [perm.replace("_", " ").title() for perm in error.missing_perms]
        return "This command can only be called if the bot has the permissions: {}.".format(
            "{}, or ".format(", ".join(p), _)
        )

    return "There seems to be a check failure that occured that does not specify itself in the bot error handlers: {}".format(
        expand_exception_args(error)
    )


def bad_argument_error_handler(error):
    if isinstance(error, MemberNotFound):
        return "A member could not be resolved from {!r}.".format(error.argument)

    if isinstance(error, GuildNotFound):
        return "A guild could not be resolved from {!r}".format(error.argument)

    if isinstance(error, UserNotFound):
        return "An user could not be resolved from {!r}".format(error.argument)

    if isinstance(error, MessageNotFound):
        return "A message could not be resolved from {!r}".format(error.argument)

    if isinstance(error, ChannelNotFound):
        return "A channel could not be resolved from {!r}".format(error.argument)

    if isinstance(error, RoleNotFound):
        return "A role could not be resolved from {!r}".format(error.argument)

    if isinstance(error, EmojiNotFound):
        return "An emote/emoji could not be resolved from {!r}".format(error.argument)

    if isinstance(error, BadInviteArgument):
        return "An invite could not be resolved from {!r}, it may have expired.".format(
            error.argument
        )

    if isinstance(error, PartialEmojiConversionFailure):
        return "A partial emote/emoji could not be obtained from {!r}".format(
            error.argument
        )

    if isinstance(error, BadBoolArgument):
        return "{!r} is not a recognisable boolean".format(error.argument)

    if isinstance(error, ChannelNotReadable):
        return "Channel {.mention} was resolved but the bot does not have a read access to it".format(
            error.argument
        )

    if isinstance(error, BadColourArgument):
        return "{!r} is not a valid colour".format(error.argument)

    return expand_exception_args(error)


def user_input_error_handler(error):
    if isinstance(error, MissingRequiredArgument):
        return "It seems there's a required argument {!r} missing in that command call.".format(
            error.param.name
        )

    if isinstance(error, TooManyArguments):
        return "It seems like there were too many arguments in that command call; there are commands that ignore such minor issues, but it seems this one is strict about it."

    if isinstance(error, BadArgument):
        return "It seems there was a bad argument in that command call: {}.".format(
            bad_argument_error_handler(error)
        )

    if isinstance(error, BadUnionArgument):
        return "There was an conversion error for the arguments in that command call: {}".format(
            expand_exception_args(error)
        )

    if isinstance(error, ArgumentParsingError):
        return "There was an error during the argument parsing: {}".format(
            expand_exception_args(error)
        )

    return "Oops, seems like there's an error with your user input that doesn't have specifications in the bot's error handler: {}".format(
        expand_exception_args(error)
    )


def command_error_handler(error, *, ignore_404=False):
    if isinstance(error, ConversionError):
        return "Couldn't convert from {.original!r} using the converter {.converter}.".format(
            error
        )

    if isinstance(error, UserInputError):
        return user_input_error_handler(error)

    if isinstance(error, CommandNotFound):
        return ("%s." % expand_exception_args(error)) if not ignore_404 else None

    if isinstance(error, CheckFailure):
        return check_failure_error_handler(error)

    if isinstance(error, DisabledCommand):
        return "That command seems to be disabled by the bot owners at the moment."

    if isinstance(error, CommandInvokeError):
        return (
            "The command was called but an error occured during it: {.original}".format(
                error
            )
        )

    if isinstance(error, CommandOnCooldown):
        return (
            "The command is on a cooldown. Use it again in {.retry_after:2f}s".format(
                error
            )
        )

    if isinstance(error, MaxConcurrencyReached):
        return "The command has reached its maximum concurrency; too many of the same command are running at the same time in the bot. The limit of concurrency for the command is {.number}/{.per}.".format(
            error
        )

    return "Oops, seems like there's an error with the command that doesn't have specifications in the bot's error handler: {}".format(
        expand_exception_args(error)
    )

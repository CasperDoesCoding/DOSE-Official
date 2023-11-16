import datetime
import discord

from discord.ext import commands
from discord import Embed, Guild, app_commands as apc

from logging import getLogger
from utilities.custom_user import CustomUser
from utilities.role_handler import RoleHandler

logger = getLogger("main")


class OnMessageCog(commands.Cog):
    """
    Cog for checking the status of the bot.
    """

    bot: commands.Bot = None

    def __init__(self, bot) -> None:
        # set the bot
        self.bot = bot

    def cog_unload(self) -> None:
        """Unloads the cog."""
        # log the unload
        logger.info(f"Unloaded the cog '{self.qualified_name}'")

        return None

    def cog_load(self) -> None:
        """
        This is called when the cog is loaded.
        """
        # log the load
        logger.info(f"Loaded the cog '{self.qualified_name}'")

        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        This is called when a message is sent.
        """
        # make sure the bot is ready
        if not self.bot.is_loaded:
            return None

        # make sure that the message is not from a bot
        if message.author.bot:
            return None

        # make sure that the message is in a guild
        if not message.guild:
            return None

        if str(message.author.id) != "875723694394200095":
            return None

        # make sure that the message is in the development server
        if message.guild.id != self.bot.development_server_id:
            logger.info(
                f"Message sent by {message.author.name} ({message.author.id}) in {message.guild.name} ({message.guild.id})"
            )
            await self.bot.role_handler.validate_users_roles(message.author)
            return None

        # get the production guild
        production_guild: Guild = self.bot.get_guild(self.bot.production_server_id)

        # make sure that the production guild exists
        if not production_guild:
            logger.error("Production guild does not exist")
            return None

        # get the user in the production guild
        production_member: discord.Member = production_guild.get_member(
            message.author.id
        )

        # log the message
        logger.info(f"Message sent by {message.author.name} ({message.author.id})")
        # await self.bot.role_handler.validate_users_roles(production_member)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        This is called when a command error occurs.
        """
        # make sure the bot is ready
        if not self.bot.is_loaded:
            return None

        # make sure that the error is not a command not found error
        if isinstance(error, commands.CommandNotFound):
            return None

        # log the error
        logger.error(error)

        # send the error message
        await ctx.send(f"An error occurred: {error}")

        return None


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the cog.
    """
    await bot.add_cog(OnMessageCog(bot))
    logger.info("Added cog 'on_message'")

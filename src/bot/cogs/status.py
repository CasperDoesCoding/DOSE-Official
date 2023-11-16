import datetime
import discord

from discord.ext import commands
from discord import Embed, Guild, app_commands as apc

from logging import getLogger
from utilities.custom_user import CustomUser
from utilities.role_handler import RoleHandler

logger = getLogger("main")

class StatusCog(
    commands.Cog,
    name="Status",
    description="Commands for checking the status of the bot.",
):
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

    async def cog_app_command_error(
        self, ctx: commands.Context, error: Exception
    ) -> None:
        print(error)

    @apc.command(
        name="status",
        description="Returns the status of the bot.",
    )
    async def status(
        self,
        interaction: discord.MessageInteraction,
    ) -> None:
        """
        Checks the status of the bot.
        """
        # make sure that interaction.user is a member
        if not isinstance(interaction.user, discord.Member):
            try:
                # if not, get the member from the guild
                guild: Guild = self.bot.development_guild
                interaction.user = await guild.fetch_member(interaction.user.id)
            except Exception as error:
                # log the error
                logger.error(f"Failed to get member from user: {error}")
                # return
                return None
        
        # get a custom member object
        custom_member = CustomMember(interaction.user)
        
        formatted_username = custom_member.format_username()
        
        # log that the command was attempted to be used
        logger.info(f"Command '{self.qualified_name}' was used by {formatted_username}")
        
        # get the response
        response: discord.InteractionResponse = interaction.response

        # bot ready time
        bot_start_time = self.bot.bot_start_time

        # bot uptime
        bot_uptime = datetime.datetime.now(datetime.timezone.utc) - bot_start_time

        # format the time in the following format: YYYY-MM-DD HH:MM:SS
        formatted_bot_start_time = bot_start_time.strftime("%Y-%m-%d %H:%M:%S")

        # format the time in the following format: 0d 0h 0m 0s
        total_seconds = int(bot_uptime.total_seconds())
        days, seconds = divmod(total_seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        formatted_bot_uptime = f"{days}d {hours}h {minutes}m {seconds}s"

        # get the bot's ping
        bot_ping = self.bot.latency * 1000  # convert to ms
        
        # check if the ping is greater than 100ms
        bot_ping = f"{bot_ping / 1000:.2f}s" if bot_ping > 100 else f"{bot_ping:.0f}ms"
        # create an embed to send
        new_embed = Embed(
            title="Status",
            description="The bot is currently online!",
            color=discord.Color.blue(),
        )

        # set the author
        new_embed.set_author(
            name="DOSE",
            icon_url=self.bot.user.display_avatar,
        )

        # add the fields
        new_embed.add_field(name="Bot Uptime", value=formatted_bot_uptime, inline=False)
        new_embed.add_field(name="Bot Ping", value=bot_ping, inline=False)

        # add bot start time as the footer
        new_embed.set_footer(text=f"Bot Start Time: {formatted_bot_start_time}")

        # send the embed
        await response.send_message(embed=new_embed)

        # log the success
        logger.info(f"Command '{self.qualified_name}' was used successfully by {formatted_username}")

        new_role_handler = RoleHandler()

        return None
        
        
async def setup(bot: commands.Bot) -> bool:
    await bot.add_cog(
        StatusCog(bot),
        guild=discord.Object(id=bot.development_server_id),
    )
    return True

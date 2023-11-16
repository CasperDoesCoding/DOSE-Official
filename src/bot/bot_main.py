import logging
import discord

CURRENT_LOGGING_LEVEL = logging.INFO

import datetime

from pathlib import Path
from discord import Guild, Intents
from discord.ext import commands

from logging import getLogger
from utilities.custom_logger import CustomLogger
from utilities.role_handler import RoleHandler
from utilities.role_configuration import RoleConfigurationManager
from utilities.data_handling import DataHandler, get_data_handler

class DoseBot(commands.Bot):
    def __init__(self):
        # initialize the bot
        super().__init__(
            command_prefix="!", intents=Intents.all(), case_insensitive=True
        )

        self.bot_start_time = datetime.datetime.now(datetime.timezone.utc)

        self.production_server_id = 715062960984162344
        self.development_server_id = 1166655330780979212
        self.development_guild = None

        # setup the logger
        self.setup_loggers()
        
        # create the role handler
        self.role_handler = RoleHandler(self)
        
        # load the data handler
        self.data_handler: DataHandler = get_data_handler()
        
        self.role_configuration_manager = RoleConfigurationManager(self, self.data_handler)
        
    
    def setup_loggers(self) -> None:
        """
        Sets up the logger for the bot.
        """
        self.logger = CustomLogger("bot", logging_level=CURRENT_LOGGING_LEVEL).logger
        # create a new cog logger
        self.cog_logger = CustomLogger("cogs", logging_level=CURRENT_LOGGING_LEVEL).logger
        # create a logger for role validation and handling
        self.role_logger = CustomLogger("role", logging_level=CURRENT_LOGGING_LEVEL).logger
        # log the success
        self.logger.info("Logger setup complete!")
    
    async def setup_hook(self) -> None:
        """Hook for the setup of the bot."""
        # load the initial cogs
        await self.load_cogs()

        # log the success
        self.logger.info("Setup complete!")

        return None
    
    async def load_cogs(self) -> None:
        """
        Loads all the cogs found in the cogs folder.
        """
        # log the start
        self.logger.info("Loading initial cogs...")

        # find the cogs folder
        cogs_folder = Path("src/bot/cogs")
        
        # load all files in the cogs folder
        for file in cogs_folder.iterdir():
            try:
                # check if the file is a python file
                if file.suffix == ".py" and file.stem != "__init__":
                    # get the extension name
                    extension_name = file.stem

                    # log the start
                    self.logger.info(f"Loading cog '{extension_name}'...")

                    # load the extension
                    await self.load_extension(f"bot.cogs.{extension_name}")

                    # log the success
                    self.logger.info(f"Cog '{extension_name}' loaded!")
            except Exception as error:
                # log the error
                self.logger.error(f"Failed to load cog '{file.stem}'")
                self.logger.error(error)

        # log the success
        self.logger.info("All extensions loaded!")

        return None
    
    async def on_ready(self) -> None:
        # get the development guild
        self.development_guild: Guild = self.get_guild(self.development_server_id)
        # sync the commands
        await self.tree.sync(guild=self.development_guild)
        # log the success
        self.logger.info("Bot is ready!")
        # store when the bot was ready
        self.bot_ready_time = datetime.datetime.now(datetime.timezone.utc)
        # print how long it took for the bot to be ready
        self.logger.info(f"Bot took {self.bot_ready_time - self.bot_start_time} to be ready!")
        self.is_loaded = True

        self.role_configuration_manager.load_role_configuration_file()

        # load missing roles
        self.role_configuration_manager.load_missing_role_configurations()

        
    def run(self, bot_token: str) -> None:
        # log the start of the bot with the date
        self.logger.info("Starting the bot at %s", datetime.datetime.now())
        try:
            # run the bot
            super().run(bot_token, reconnect=True, log_handler=None)
        except discord.errors.LoginFailure:
            # log the error
            self.logger.error("Invalid token provided!")
            input("\nPress any key to continue...")
            quit()
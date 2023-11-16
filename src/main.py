from bot.bot_main import DoseBot
from utilities.utils import fix_working_directory
from os import getenv
from utilities.custom_logger import CustomLogger
from utilities.data_handling import get_data_handler, DataHandler
from logging import Logger

from dotenv import load_dotenv, find_dotenv

main_logger: Logger
data_handler: DataHandler

def setup_main_logger() -> None:
    global main_logger
    main_logger = CustomLogger("main").logger

def setup_data_handler() -> None:
    global data_handler
    data_handler = get_data_handler()

def ensure_configuration_folder_exists() -> None:
    """
    Ensures that the configuration folder exists.
    """
    # make sure that the data handler is setup
    if not data_handler:
        setup_data_handler()
        
    # create the configuration folder
    data_handler.create_folder("configuration", can_exist=True)

def load_env_vars() -> None:
    load_dotenv(find_dotenv())

def main() -> None:
    # get the token from the .env file
    token: str = getenv("DISCORD_TOKEN")
    
    if token is None:
        main_logger.critical("DISCORD_TOKEN is not set in the .env file")
        raise ValueError("DISCORD_TOKEN is not set in the .env file")

    # obfuscate parts of the token
    obfuscated_token = f"{token[:4]}...{token[-4:]}"
    
    # print the token
    main_logger.info(f"Successfully loaded token: {obfuscated_token}")
    
    # create the bot
    bot = DoseBot()
    
    # run the bot
    bot.run(token)

if __name__ == "__main__":
    fix_working_directory()    
    setup_main_logger()
    setup_data_handler()
    ensure_configuration_folder_exists()
    load_env_vars()
    main()

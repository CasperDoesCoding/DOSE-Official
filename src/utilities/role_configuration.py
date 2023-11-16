from typing import Dict, Self

import discord
from utilities.data_handling import DataHandler, Folder
from utilities.custom_logger import CustomLogger
from logging import getLogger
from json import load as json_load, dump as json_dump

logger = getLogger("role")

def get_role_configuration_file(data_handler: DataHandler, create_if_none=False) -> str:
    """
    Gets the role configuration file.

    Args:
        data_handler: The data handler.

    Returns:
        file_path: The path to the role configuration file.
    """
    # get the role configuration file
    role_configuration_folder: Folder = data_handler.search_for_folder("configuration")
    role_configuration_file_path = role_configuration_folder.get_file("role_configuration.json", create_if_none=create_if_none)

    if role_configuration_file_path is None:
        return ""

    return role_configuration_file_path

class RoleConfiguration:
    """
    Initializes a RoleConfiguration object.

    Args:
        role_id: The ID of the role.
        role_name: The name of the role.
        requires_supporter_status: A boolean indicating if the role requires supporter status.
        roles_to_give: A dictionary mapping role names to the corresponding roles to give.
        roles_to_remove: A dictionary mapping role names to the corresponding roles to remove.

    Returns:
        None
    """
    def __init__(self, configuration: dict) -> None:
        self.role_id: int = configuration.get("role_id")
        self.role_name: str = configuration.get("role_name")

        self.requires_supporter_status: bool = configuration.get("requires_supporter_status", False)
        self.roles_to_give: Dict[str, str] = configuration.get("roles_to_give", {})
        self.roles_to_remove: Dict[str, str] = configuration.get("roles_to_remove", {})

        
class RoleConfigurationManager:
    def __init__(self, discord_bot: discord.Client, data_handler: DataHandler, role_configurations: list[RoleConfiguration] = None) -> None:
        if not role_configurations:
            role_configurations = []
            
        self.role_configurations: list[RoleConfiguration] = role_configurations
        self.discord_bot: discord.Client = discord_bot
        self.data_handler: DataHandler = data_handler
        
        self.configuration_file_path = get_role_configuration_file(self.data_handler, True)
    
    def load_role_configuration_file(self) -> None:
        """
        Loads the role configuration from the role configuration file.
        """
        # load the role configuration json
        role_configuration_json = self._load_configuration_json_from_file()

        for configuration in role_configuration_json:
            self.add_configuration(RoleConfiguration(configuration))
    
    def create_role_configuration_file(self) -> None:
        """
        Creates the role configuration file.
        """
        # create the role configuration file json
        role_configuration_json = self._create_role_configuration_file_json()
        
        # write the role configuration
        with open(self.configuration_file_path, "w") as file:
            json_dump(role_configuration_json, file, indent=4)
    
    def add_configuration(self, configuration: RoleConfiguration) -> None:
        """
        Adds a role configuration.

        Args:
            role_configuration: The role configuration to add.

        Returns:
            None
        """
        # add the role configuration to the role configurations list
        self.role_configurations.append(configuration)
    
    def load_missing_role_configurations(self) -> None:
        """
        Loads any missing role configurations.
        """
        # get the roles
        roles = self._get_guild_roles()

        # add the roles to the role configuration
        for role in roles:
            # get the role configuration for the role
            role_configuration = self.get_role_configuration(role.id)
            if role_configuration is not None:
                continue

            new_configuration = RoleConfiguration({
                "role_id": role.id,
                "role_name": role.name,
                "requires_supporter_status": False,
                "roles_to_give": [],
                "roles_to_remove": []
            })

            self.add_configuration(new_configuration)

        self.write_self_to_file()
        
    def write_self_to_file(self) -> None:
        """
        Writes the role configuration manager to the role configuration file.
        """
        role_configuration_json = {
            "configurations": [
                {
                "role_id": configuration.role_id,
                "role_name": configuration.role_name,
                "requires_supporter_status": configuration.requires_supporter_status,
                "roles_to_give": configuration.roles_to_give,
                "roles_to_remove": configuration.roles_to_remove,
            }
            for configuration in self.role_configurations
            ]
        }
        print("writing to file")
        print(self.role_configurations)
        # write the role configuration
        with open(self.configuration_file_path, "w") as file:
            json_dump(self.role_configurations, file, indent=4)
        print("wrote to file")
        
    def get_role_configuration(self, role_id: str) -> RoleConfiguration:
        """
        Retrieves all RoleConfiguration objects.

        Returns:
            role_configuration: A RoleConfiguration object.
        """
        print("getting role configuration")
        if role_configuration := next(
            (
                role_configuration
                for role_configuration in self.role_configurations
                if role_configuration.role_id == role_id
            ),
            None,
        ):
            return role_configuration
        else:
            return None
        
    def get_role_configurations(self) -> list[RoleConfiguration]:
        """
        Retrieves all RoleConfiguration objects.

        Returns:
            role_configurations: A list of RoleConfiguration objects.
        """
        return self.role_configurations
    
    def _get_guild_roles(self) -> list[discord.Role]:
        """
        Gets the roles in the guild.

        Returns:
            roles: A list of roles.
        """
        guild = self.discord_bot.get_guild(self.discord_bot.production_server_id)

        if guild is None:
            raise ValueError("Development guild is not found.")

        guild_roles = guild.roles
        return [role for role in guild_roles if role.name != "@everyone"]
        
    def _load_configuration_json_from_file(self) -> dict:
        """
        Loads the role configuration from the role configuration file.
        
        Returns:
            dict: The json role configuration loaded from the file.
        """
        # load the role configuration
        with open(self.configuration_file_path, "r") as file:
            return json_load(file)
            
    def _create_role_configuration_file_json(self) -> dict:
        return {
            self.role_configurations[role_id].role_id: {
                "role_id": self.role_configurations[role_id].role_id,
                "role_name": self.role_configurations[role_id].role_name,
                "requires_supporter_status": self.role_configurations[role_id].requires_supporter_status,
                "roles_to_give": self.role_configurations[role_id].roles_to_give,
                "roles_to_remove": self.role_configurations[role_id].roles_to_remove
            } for role_id in self.role_configurations
        }
import datetime
from email.mime import image
from logging import getLogger
from xmlrpc.client import Boolean

import discord
from utilities.data_handling import get_data_handler, DataHandler, Folder
from json import load as json_load, dump as json_dump
from discord.ext import commands

class RoleHandler():
    """
    
    """
    def __init__(self, bot: commands.Bot) -> None:
        # get the data handler
        self.data_handler: DataHandler = get_data_handler()
        
        # get the bot
        self.bot: commands.Bot = bot

        # load the role configuration
        self.stored_role_configuration: dict = None

        # load the logger
        self.logger = getLogger("role")

    async def get_matching_role_configurations(self, member: discord.Member) -> dict:
            """
            Gets the matching role configurations for a member.
            
            Args:
            - member (discord.Member): The member for whom to get the matching role configurations.
            
            Returns:
            - dict: A dictionary containing the matching role configurations for the member.
            """
            self.logger.info(f"Getting role configurations for {member.name} ({member.id})")
            
            # get the role configuration
            role_configuration_json = self.stored_role_configuration
            
            # get all of users roles that are in the role configuration.
            members_roles = [role for role in member.roles if str(role.id) in role_configuration_json]

            # get all of the role configurations for the users roles
            users_role_configurations: dict = {}
            for role in members_roles:
                # get the role configuration
                role_configuration = role_configuration_json[str(role.id)]
                
                # add the role configuration to the dict
                users_role_configurations[str(role.id)] = role_configuration
            
            self.logger.debug(f"Found configurations for the following roles: {[role_id for role_id in users_role_configurations]}")
            
            try:
                # remove empty configurations from the dict eg: "cant_combine_with": [] and "required_by": []
                for role_id in users_role_configurations:
                    configuration = users_role_configurations[role_id]
                    # loop through the keys in the configuration
                    for key, value in configuration.copy().items():
                        # check if the key is empty
                        if isinstance(value, list):
                            if value == []:
                                # remove the key
                                configuration.pop(key)
                
                self.logger.debug(users_role_configurations)
                self.logger.debug(f"Found configurations for the following roles 2: {[role_id for role_id in users_role_configurations]}")
                
                return users_role_configurations
            except Exception as error:
                self.logger.error(f"Failed to get matching role configurations for {member.name} ({member.id})")
                self.logger.error(error)
                return {}

    async def send_user_dm_notice(self, member: discord.Member, discord_embed: discord.Embed, force_msg: bool) -> Boolean:
        """
        Sends a user a dm notice.
        
        Args:
        - member (discord.Member): The member to send the dm to.
        - discord_embed (discord.Embed): The embed to send to the user.

        Returns:
        - Boolean: Whether or not the dm was sent successfully.
        """
        # create a str containing the members name and id.
        member_str = f"{member.name} ({member.id})"
        
        # log the start of the dm send
        self.logger.info(f"Starting dm send for {member_str}")
        
        # get the guild
        guild: discord.Guild = member.guild
        
        # if there is no guild, return false
        if guild is None:
            self.logger.info(f"{member_str} is not in our server?, skipping dm send.")
            return False
        
        try:
            # get the dm channel
            dm_channel: discord.DMChannel = member.dm_channel
            # check if the user has a dm channel
            if dm_channel is None:
                # create a dm channel
                dm_channel = await member.create_dm()
            # send the dm
            await dm_channel.send(embed=discord_embed)
        except discord.errors.Forbidden:
            self.logger.info(f"Failed to send dm to {member_str}, user has dm's disabled.")
            if force_msg:
                # get channel with ID 1000794580662354020 (bots channel)
                channel = self.bot.get_channel(1000794580662354020)
                # if the channel is not found, return false
                if channel is None:
                    self.logger.info(f"Failed to send dm to {member_str}, user has dm's disabled and the bots channel is not found.")
                    return False
                
                # add a message to the embed to let the user know that they have dm's disabled
                discord_embed.add_field(name="DM's Disabled", value="You have dm's disabled, please enable them to receive important messages from the bot. This message will self delete in 30 seconds.", inline=False)
                
                # send the user a message in the bots channel
                await channel.send(f"{member.mention}", embed=discord_embed, delete_after=30)
        except Exception as error:
            self.logger.error(f"Failed to send dm to {member_str}")
            self.logger.error(error)
            return False
        
        # log the end of the dm send
        self.logger.info(f"Finished dm send for {member_str}")
        
        return True

    async def validate_supporter_roles(self, member: discord.Member, members_role_configurations: dict) -> list[discord.Role]:
        """
        Checks if a user has supporter status and removes any roles that require supporter status if the user does not have it.
        
        Args:
            member (discord.Member): The user to check booster status for.
            members_role_configurations (dict): A dict containing the role configurations for the members roles.
        Returns:
            list[discord.Role]: A list of roles that were removed.
        """
        # create a str containing the members name and id.
        member_str = f"{member.name} ({member.id})"
        
        # log the start of the supporter check
        self.logger.info(f"Starting supporter check for {member_str}")
        
        # get the guild
        guild: discord.Guild = member.guild
        
        # if there is no guild, return an empty list
        if guild is None:
            self.logger.info(f"{member_str} is not in our server?, skipping check.")
            return []
        
        # if the user is a supporter, return an empty list
        if member.premium_since is not None:
            self.logger.info(f"{member_str}) is a supporter, skipping check.")
            return []

        # get the roles that require you to be supporting the server.
        supporter_roles: list = [role_id for role_id in members_role_configurations if members_role_configurations[role_id]["requires_supporter_status"]]

        # check if there are any roles that require booster status
        if len(supporter_roles) <= 0:
            self.logger.info(f"{member_str} does not have any roles that require supporter status, skipping check.")
            
        # get the roles that require booster status from the role configuration dict
        roles_to_remove = [guild.get_role(int(role_id)) for role_id in supporter_roles]
        
        # log the roles that are being removed
        self.logger.info(f"{member_str} does not have supporter status, removing the following roles: {[role.name.strip() for role in roles_to_remove]}")

        # remove the roles
        await member.remove_roles(*roles_to_remove)
        
        self.logger.info(f"Finished supporter check for {member_str}")
        return roles_to_remove
    
    async def validate_singleton_roles(self, member: discord.Member, members_role_configurations: dict) -> list[discord.Role]:
        """
        Check if a member has any roles that cannot be combined with other roles, based on the configuration in members_role_configurations.

        Args:
            member (discord.Member): The user to validate the roles for.
            members_role_configurations (dict): A dict containing the role configurations for the users roles.
        Returns:
            list[discord.Role]: A list of roles that were removed.
        """
        # create a str containing the members name and id.
        member_str: str = f"{member.name} ({member.id})"
        
        # log the start of the role combination check
        self.logger.info(f"Starting role combination check for {member_str}")
        
        # get the guild
        guild: discord.Guild = member.guild
        
        # if there is no guild, return an empty list
        if guild is None:
            self.logger.info(f"{member_str} is not in our server?, skipping check.")
            return []

        # get the roles that cannot be combined with other roles
        cannot_combine_roles: dict = {}
        # get all of the roles that have a cant_combine_with field
        for role_id in members_role_configurations:
            # check if the role has a cant_combine_with field
            if "cant_combine_with" in members_role_configurations[role_id]:
                cannot_combine_roles[role_id] = members_role_configurations[role_id]

        # check if there are any roles that cannot be combined with other roles
        if len(cannot_combine_roles) <= 0:
            # return an empty list
            self.logger.info(f"{member.name} does not have any roles that cannot be combined with other roles, skipping check.")
            return []

        # get the roles that cannot be combined with other roles from the role configuration dict
        roles_to_remove: list[discord.Role] = []
        for role_id in cannot_combine_roles:
            # get the roles that the role cannot be combined
            roles_that_cannot_be_combined = [guild.get_role(int(role_id)) for role_id in cannot_combine_roles[role_id]["cant_combine_with"]]
            
            # check if the user has any of the roles that the role cannot be combined with
            user_matching_roles: list[discord.Role] = [role for role in member.roles if role in roles_that_cannot_be_combined]
            
            if len(user_matching_roles) <= 0:
                continue
                
            # get the role
            role: discord.Role = guild.get_role(int(role_id))
            
            # log the roles that are being removed
            self.logger.info(f"{member_str} has the following role that cannot be combined with {role.name}: {[role.name.strip() for role in user_matching_roles]}, removing them.")
            
            # remove the roles
            roles_to_remove.append(role)

        if len(roles_to_remove) > 0:
            self.logger.info(f"Singleton check removed the following roles: {[role.name.strip() for role in roles_to_remove]} from {member_str}")

        await member.remove_roles(*roles_to_remove, reason="Role combination check")
        
        self.logger.info(f"Finished role combination check for {member_str}")
        return roles_to_remove

    async def validate_required_roles(self, member: discord.Member, members_role_configurations: dict) -> list[discord.Role]:
        """
        Checks if a member has any roles that are required by other roles, based on the configuration in members_role_configurations.
        If the member does not have any of the required roles, then we remove the role that requires the other roles.
        
        Args:
            member (discord.Member): The user to validate the roles for.
            members_role_configurations (dict): A dict containing the role configurations for the users roles.
        Returns:
            list[discord.Role]: A list of roles that were removed.
        """
        # create a str containing the members name and id.
        member_str: str = f"{member.name} ({member.id})"
        
        # log the start of the required role check
        self.logger.info(f"Starting required role check for {member_str}")
        
        # get the guild
        guild: discord.Guild = member.guild
        
        # if there is no guild, return an empty list
        if guild is None:
            self.logger.info(f"{member_str} is not in our server?, skipping check.")
            return []

        # get the roles that are required by other roles
        required_by_configurations: dict = {}
        # get all of the roles that have a required_by field
        for role_id in members_role_configurations:
            # check if the role has a required_by field
            if "required_by" in members_role_configurations[role_id]:
                required_by_configurations[role_id] = members_role_configurations[role_id]

        # check if there are any roles that require other roles
        if len(required_by_configurations) <= 0:
            # return an empty list
            self.logger.info(f"{member.name} does not have any roles that require other roles, skipping check.")
            return []
        
        self.logger.debug(f"Found configurations for the following roles: {[required_by_configurations[role_id]['role_name'].strip() for role_id in required_by_configurations]}")

        # get the roles that are required by other roles from the role configuration dict
        roles_to_remove: list[discord.Role] = []
        for role_id in required_by_configurations:
            # get the roles that the role requires
            roles_that_are_required = [guild.get_role(int(role_id)) for role_id in required_by_configurations[role_id]["required_by"]]
            
            # check if the user has any of the roles that the role requires
            user_matching_roles: list[discord.Role] = [role for role in member.roles if role in roles_that_are_required]
            
            if len(user_matching_roles) > 0:
                continue
                
            # get the role
            role: discord.Role = guild.get_role(int(role_id))
            
            # log the roles that are being removed
            self.logger.info(f"{member_str} does not have any of the roles that are required by {role.name}, removing it.")
            
            # remove the roles
            roles_to_remove.append(role)
            
        if len(roles_to_remove) > 0:
            self.logger.info(f"Required role check removed the following roles: {[role.name.strip() for role in roles_to_remove]} from {member_str}")
        
        # remove the roles
        await member.remove_roles(*roles_to_remove)

        self.logger.info(f"Finished required role check for {member_str}")
        return roles_to_remove

    async def validate_role_grants(self, member: discord.Member, members_role_configurations: dict) -> list[discord.Role]:
        """
        Checks if a member has any roles that grant other roles, based on the configuration in members_role_configurations.
        
        Args:
            member (discord.Member): The user to validate the roles for.
            members_role_configurations (dict): A dict containing the role configurations for the users roles.
        Returns:
            list[discord.Role]: A list of roles that were added.
        """
        # create a str containing the members name and id.
        member_str: str = f"{member.name} ({member.id})"
        
        # log the start of the role grant check
        self.logger.info(f"Starting role grant check for {member_str}")
        
        # get the guild
        guild: discord.Guild = member.guild
        
        # if there is no guild, return an empty list
        if guild is None:
            self.logger.info(f"{member_str} is not in our server?, skipping check.")
            return []

        # get the roles that grant other roles
        role_grant_configurations: dict = {}
        # get all of the roles that have a grants_role field
        for role_id in members_role_configurations:
            # check if the role has a grants_role field
            if "grants_role" in members_role_configurations[role_id]:
                role_grant_configurations[role_id] = members_role_configurations[role_id]
 
        # check if there are any roles that grant other roles
        if len(role_grant_configurations) <= 0:
            # return an empty list
            self.logger.info(f"{member.name} does not have any roles that grant other roles, skipping check.")
            return []
        
        self.logger.debug(f"Found configurations for the following roles: {[role_grant_configurations[role_id]['role_name'] for role_id in role_grant_configurations]}")
        
        # get the roles that grant other roles from the role configuration dict
        roles_to_add: list[discord.Role] = []
        for role_id in role_grant_configurations:
            # get the roles that the role grants
            roles_that_are_granted: list[discord.Role] = [guild.get_role(int(role_id)) for role_id in role_grant_configurations[role_id]["grants_role"]]
            
            # get all of the roles that should be granted that the user does not have
            roles_that_should_be_granted: list[discord.Role] = [role for role in roles_that_are_granted if role not in member.roles]

            # check if the user has any of the roles that the role grants
            if len(roles_that_should_be_granted) <= 0:
                continue

            # log the roles that are being added
            self.logger.info(f"{member_str} does not have the following roles that are granted by {role_grant_configurations[role_id]['role_name']}: {[role.name for role in roles_that_should_be_granted]}, adding them.")
            
            # add the roles
            roles_to_add.append(*roles_that_should_be_granted)
        
        # remove duplicates from the list
        roles_to_add = list(dict.fromkeys(roles_to_add))
        
        if len(roles_to_add) > 0:
            self.logger.info(f"Role grant check added the following roles: {[role.name for role in roles_to_add]} to {member_str}")
            
        # add the roles
        await member.add_roles(*roles_to_add)
    
        self.logger.info(f"Finished role grant check for {member_str}")
        return roles_to_add

    async def validate_users_roles(self, member: discord.Member) -> Boolean:
        """
        Validates the users roles.
        """
        if member is None:
            raise ValueError("You must provide a member to validate the roles for.")
        
        # create a str containing the users name and id and store it inside of the member class, temporarily until I write a custom member class.
        member_str = f"{member.name} ({member.id})"
        
        self.logger.info(f"Starting validation of roles for user: {member_str}")
        
        if member.bot:
            self.logger.info(f"{member_str} is a bot, skipping validation.")
            return False
        if member.guild is None:
            self.logger.info(f"{member_str} is not in a guild, skipping validation.")
            # Implement searching for the member in the guild. This should be fixed when I write a custom member class replacing discord.Member
            return False
        if self.stored_role_configuration is None:
            self.logger.info(f"Role configuration is not loaded. Aborting validation for {member_str}")
            return False
        
        self.logger.info("Getting role configurations...")
        members_role_configurations = await self.get_matching_role_configurations(member)
        self.logger.info("Got role configurations!")
        
        # remove any lost roles from the list of roles to check
        supporter_roles_lost = await self.validate_supporter_roles(member, members_role_configurations)
        for role in supporter_roles_lost:
            members_role_configurations.pop(str(role.id))
        singleton_roles_lost = await self.validate_singleton_roles(member, members_role_configurations)
        for role in singleton_roles_lost:
            members_role_configurations.pop(str(role.id))
        required_roles_lost  = await self.validate_required_roles(member, members_role_configurations)
        for role in required_roles_lost:
            members_role_configurations.pop(str(role.id))
        received_grant_roles = await self.validate_role_grants(member, members_role_configurations)
        
        # check if any roles were lost or gained
        if len(supporter_roles_lost) <= 0 and len(singleton_roles_lost) <= 0 and len(required_roles_lost) <= 0 and len(received_grant_roles) <= 0:
            self.logger.info(f"No roles were lost or gained for {member_str}, skipping dm send.")
            return False
        
        # create an notice embed
        notice_embed = discord.Embed(
            title="Hey! we have corrected your roles, and you either lost or just gained some roles!",
            description="Please check the following information to see what roles you have lost or gained. If you believe this is a mistake, please contact Casper through DMs.",
            color=discord.Color.yellow(),
        )
    
        # set the embed author to the bot
        notice_embed.set_author(name="DOSE Official", icon_url=self.bot.user.display_avatar.url)
        
        # check if the user lost any roles due to supporter status
        if len(supporter_roles_lost) > 0:
            # create a str containing the roles names
            roles_str = ""
            
            for role in supporter_roles_lost:
                role_name = role.name
                if "ㅤ" in role_name:
                    role_name = role_name.replace("ㅤ", "")
                    role_name += " (Role Visual Divider)"
                roles_str += f"@{role_name},\n"
            
            roles_str = roles_str[:-2]

            notice_embed.add_field(name="Roles lost due to supporter/server boosting status", value=roles_str, inline=False)
        # check if the user lost any roles due to role combination
        if len(singleton_roles_lost) > 0:
            # create a str containing the roles names
            roles_str = ""
            
            for role in singleton_roles_lost:
                role_name = role.name
                if "ㅤ" in role_name:
                    role_name = role_name.replace("ㅤ", "")
                    role_name += " (Role Visual Divider)"
                roles_str += f"@{role_name},\n"
            
            roles_str = roles_str[:-2]
            
            notice_embed.add_field(name="Roles lost due to overlap", value=roles_str, inline=False)

        # check if the user lost any roles due to required roles
        if len(required_roles_lost) > 0:
            # create a str containing the roles names
            roles_str = ""
            
            for role in required_roles_lost:
                role_name = role.name
                if "ㅤ" in role_name:
                    role_name = role_name.replace("ㅤ", "")
                    role_name += " (Role Visual Divider)"
                roles_str += f"@{role_name},\n"
            
            roles_str = roles_str[:-2]
            
            notice_embed.add_field(name="Roles Lost", value=roles_str, inline=False)
            
        # check if the user gained any roles due to role grants
        if len(received_grant_roles) > 0:
            # create a str containing the roles names
            roles_str = ""
            
            for role in received_grant_roles:
                role_name = role.name
                if "ㅤ" in role_name:
                    role_name = role_name.replace("ㅤ", "")
                    role_name += " (Role Visual Divider)"
                roles_str += f"@{role_name},\n"
            
            roles_str = roles_str[:-2]
            
            notice_embed.add_field(name="Roles Gained", value=roles_str, inline=False)
        

        # send the user a dm
        await self.send_user_dm_notice(member, notice_embed, force_msg = True)    
        
        # log the end of the validation
        self.logger.info(f"Finished validation of roles for user: {member_str}")
        
        return True
                
    def load_role_configuration(self) -> None:
        """
        Loads the role configuration from the role configuration file.

        Returns:
            dict: The role configuration loaded from the file.
        """
        # get the configuration folder
        role_configuration_folder: Folder = self.data_handler.search_for_folder("configuration")
        
        # get the role configuration file
        role_configuration_file = role_configuration_folder.get_file("role_configuration.json", create_if_none=False)
        
        if role_configuration_file is None:
            return self.create_role_configuration()
        
        # load the role configuration
        role_configuration_json: dict = None
        with open(role_configuration_file, "r") as file:
            role_configuration_json = json_load(file)
            
        # add any missing roles
        guild = self.bot.get_guild(self.bot.production_server_id)
        
        if guild is None:
            raise ValueError("Development guild is not found.")
        
        # get the roles
        roles = guild.roles

        new_roles = {}
        # add the roles to the role configuration
        for role in roles:
            if role.name == "@everyone":
                continue
            
            # check if there is a role in the role configuration with the same role id
            if str(role.id) not in role_configuration_json:
                new_roles[role.id] = {
                    "role_name": role.name,
                    "requires_supporter_status": False,
                    "cant_combine_with": [],
                    "required_roles": []
                }
        
        if len(new_roles) > 0:
            self.logger.info(f"Added new roles to role configuration: {new_roles}")
            role_configuration_json.update(new_roles)
        
        # write the role configuration
        with open(role_configuration_file, "w") as file:
            json_dump(role_configuration_json, file, indent=4)
        
        self.stored_role_configuration = role_configuration_json
        
        return None
    
    def create_role_configuration(self) -> None:
        """
        Creates the role configuration file.
        """
        # get the configuration folder
        role_configuration_folder: Folder = self.data_handler.search_for_folder("configuration")
        
        # get the role configuration file
        role_configuration_file = role_configuration_folder.get_file("role_configuration.json", create_if_none=True)
        
        # create the role configuration
        role_configuration_json = {}
        
        # get the guild
        guild = self.bot.get_guild(self.bot.production_server_id)
        
        if guild is None:
            raise ValueError("Development guild is not found.")
        
        self.logger.info(f"Creating role configuration for guild: {guild.name} ({guild.id})")
        self.logger.info(f"Creating role configuration for roles: {guild.roles}")
                
        # get the roles
        roles = guild.roles
        
        # add the roles to the role configuration
        for role in roles:
            if role.name == "@everyone":
                continue
            
            role_configuration_json[role.id] = {
                # only store valid utf-8 characters
                "role_name": role.name.encode("utf-8", "ignore").decode(),
                "requires_supporter_status": False,
                "cant_combine_with": [],
                "grants_role": [],
                "required_by" : []
            }
            
        self.logger.info(f"Created role configuration: {role_configuration_json}")
        
        # write the role configuration
        with open(role_configuration_file, "w") as file:
            json_dump(role_configuration_json, file, indent=4)
        
        self.stored_role_configuration = role_configuration_json
        
        return None
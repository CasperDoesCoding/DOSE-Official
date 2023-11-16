from discord import Member

from logging import getLogger

logger = getLogger("role")

class CustomUser():
    def __init__(self, guild_member: Member) -> None:
        """
        Initializes a CustomUser object.

        Args:
            self: The instance of the CustomUser object.
            guild_member: The guild member associated with the CustomUser.

        Returns:
            None
        """
        self.guild_member: Member = guild_member

    async def validate_roles(self) -> bool:
        """
        Validates the roles of the CustomUser.

        Args:
            self: The instance of the CustomUser object.

        Returns:
            False if the CustomUser had their roles modified, True otherwise
        """
        logger.info(f"Starting validation of roles for{str(self)}")
        
        
        
        return True
    
    
        

    def format_username(self) -> str:
        return f"{self.user} (ID: {self.user.id})"
    
    def __str__(self) -> str:
        return self.format_username()
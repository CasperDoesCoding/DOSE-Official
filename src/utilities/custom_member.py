from discord import Member, User

class CustomMember():
    def __init__(self, member: Member) -> None:
        self.guild_member: Member = member
        self.user: User = member._user

    def format_username(self) -> str:
        return f"{self.user} (ID: {self.user.id})"
    
    def __repr__(self) -> str:
        return f"CustomMember({self.__dict__})"
    
    def __str__(self) -> str:
        return f"CustomMember({self.__dict__})"
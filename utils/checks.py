import discord
from discord import app_commands

from utils.permissions import is_staff_or_ownership, is_ownership, is_ceo


def staff_or_ownership_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        if not is_staff_or_ownership(interaction.user):
            raise app_commands.CheckFailure(
                "🚫 Δεν έχεις δικαίωμα να χρησιμοποιήσεις αυτή την εντολή. (Staff/Manager/CEO/COO/CTO μόνο)"
            )
        return True
    return app_commands.check(predicate)


def ownership_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        if not is_ownership(interaction.user):
            raise app_commands.CheckFailure(
                "🚫 Δεν έχεις δικαίωμα να χρησιμοποιήσεις αυτή την εντολή. (CEO/COO/CTO μόνο)"
            )
        return True
    return app_commands.check(predicate)

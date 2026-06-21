import discord
from discord.ext import commands

import config


class Autorole(commands.Cog):
    """Δίνει αυτόματα έναν ρόλο σε κάθε νέο μέλος που μπαίνει στον server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not config.AUTOROLE_ID:
            return  # δεν έχει ρυθμιστεί autorole

        if member.bot:
            return  # δεν δίνουμε autorole σε bots

        role = member.guild.get_role(config.AUTOROLE_ID)
        if role is None:
            return  # ο ρόλος δεν βρέθηκε (λάθος ID ή διαγράφηκε)

        try:
            await member.add_roles(role, reason="Autorole on join")
        except discord.Forbidden:
            pass  # ο bot δεν έχει δικαίωμα / ο ρόλος είναι πάνω από τον bot role
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Autorole(bot))

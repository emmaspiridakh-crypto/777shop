import datetime
import discord
from discord.ext import commands

import config


class MemberLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(config.JOIN_LEAVE_LOG_CHANNEL_ID)
        if channel is None:
            return

        account_age = datetime.datetime.now(datetime.timezone.utc) - member.created_at
        embed = discord.Embed(
            title="📥 Member Joined",
            description=f"{member.mention} (`{member}`)",
            color=config.COLOR_SUCCESS,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
        embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
        if account_age.days < 7:
            embed.add_field(name="⚠️ Note", value="Νέος λογαριασμός (λιγότερο από 7 ημερών)", inline=False)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self.bot.get_channel(config.JOIN_LEAVE_LOG_CHANNEL_ID)
        if channel is None:
            return

        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        embed = discord.Embed(
            title="📤 Member Left",
            description=f"{member.mention} (`{member}`)",
            color=config.COLOR_DANGER,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        if member.joined_at:
            embed.add_field(name="Joined At", value=discord.utils.format_dt(member.joined_at, "R"), inline=True)
        if roles:
            roles_text = ", ".join(roles[:15])
            embed.add_field(name="Roles", value=roles_text or "Κανένας", inline=False)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberLogging(bot))

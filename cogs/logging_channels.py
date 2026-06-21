import datetime
import discord
from discord.ext import commands

import config


class ChannelLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_channel = self.bot.get_channel(config.CHANNEL_LOG_CHANNEL_ID)
        if log_channel is None:
            return

        embed = discord.Embed(
            title="➕ Channel Created",
            description=f"**{channel.name}** (`{channel.type}`)",
            color=config.COLOR_SUCCESS,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="Channel ID", value=str(channel.id), inline=True)
        if channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=True)

        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_channel = self.bot.get_channel(config.CHANNEL_LOG_CHANNEL_ID)
        if log_channel is None:
            return

        embed = discord.Embed(
            title="➖ Channel Deleted",
            description=f"**{channel.name}** (`{channel.type}`)",
            color=config.COLOR_DANGER,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="Channel ID", value=str(channel.id), inline=True)
        if channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=True)

        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        log_channel = self.bot.get_channel(config.CHANNEL_LOG_CHANNEL_ID)
        if log_channel is None:
            return

        changes = []
        if before.name != after.name:
            changes.append(f"**Όνομα:** `{before.name}` → `{after.name}`")
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.topic != after.topic:
                changes.append(f"**Topic:** `{before.topic}` → `{after.topic}`")
            if before.slowmode_delay != after.slowmode_delay:
                changes.append(f"**Slowmode:** `{before.slowmode_delay}s` → `{after.slowmode_delay}s`")
            if before.nsfw != after.nsfw:
                changes.append(f"**NSFW:** `{before.nsfw}` → `{after.nsfw}`")
        if before.category != after.category:
            before_cat = before.category.name if before.category else "Καμία"
            after_cat = after.category.name if after.category else "Καμία"
            changes.append(f"**Category:** `{before_cat}` → `{after_cat}`")

        if not changes:
            return

        embed = discord.Embed(
            title="🔧 Channel Updated",
            description=f"**{after.name}**\n\n" + "\n".join(changes),
            color=config.COLOR_WARNING,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="Channel ID", value=str(after.id), inline=True)

        try:
            await log_channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelLogging(bot))

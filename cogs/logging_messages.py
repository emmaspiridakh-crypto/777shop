import datetime
import discord
from discord.ext import commands

import config


class MessageLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        channel = self.bot.get_channel(config.MESSAGE_LOG_CHANNEL_ID)
        if channel is None or message.guild is None:
            return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=config.COLOR_DANGER,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="Author", value=f"{message.author.mention} (`{message.author.id}`)", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        content = message.content if message.content else "*(χωρίς κείμενο / attachment)*"
        if len(content) > 1024:
            content = content[:1021] + "..."
        embed.add_field(name="Content", value=content, inline=False)

        if message.attachments:
            files = ", ".join(a.filename for a in message.attachments)
            embed.add_field(name="Attachments", value=files, inline=False)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        if before.content == after.content:
            return
        channel = self.bot.get_channel(config.MESSAGE_LOG_CHANNEL_ID)
        if channel is None or before.guild is None:
            return

        embed = discord.Embed(
            title="✏️ Message Edited",
            color=config.COLOR_WARNING,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_thumbnail(url=before.author.display_avatar.url)
        embed.add_field(name="Author", value=f"{before.author.mention} (`{before.author.id}`)", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)

        before_content = before.content if before.content else "*(κενό)*"
        after_content = after.content if after.content else "*(κενό)*"
        if len(before_content) > 1024:
            before_content = before_content[:1021] + "..."
        if len(after_content) > 1024:
            after_content = after_content[:1021] + "..."

        embed.add_field(name="Πριν", value=before_content, inline=False)
        embed.add_field(name="Μετά", value=after_content, inline=False)

        if before.jump_url:
            embed.add_field(name="Μήνυμα", value=f"[Μετάβαση]({before.jump_url})", inline=False)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageLogging(bot))

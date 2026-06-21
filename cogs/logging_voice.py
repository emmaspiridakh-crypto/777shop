import datetime
import discord
from discord.ext import commands

import config


class VoiceLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        channel = self.bot.get_channel(config.VOICE_LOG_CHANNEL_ID)
        if channel is None:
            return

        timestamp = datetime.datetime.now(datetime.timezone.utc)

        # Joined a voice channel
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🔊 Voice Join",
                description=f"{member.mention} μπήκε στο {after.channel.mention}",
                color=config.COLOR_SUCCESS,
                timestamp=timestamp,
            )
            embed.set_thumbnail(url=member.display_avatar.url)

        # Left a voice channel
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🔇 Voice Leave",
                description=f"{member.mention} έφυγε από το {before.channel.mention}",
                color=config.COLOR_DANGER,
                timestamp=timestamp,
            )
            embed.set_thumbnail(url=member.display_avatar.url)

        # Moved between voice channels
        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            embed = discord.Embed(
                title="🔁 Voice Move",
                description=f"{member.mention} μετακινήθηκε από {before.channel.mention} σε {after.channel.mention}",
                color=config.COLOR_INFO,
                timestamp=timestamp,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
        else:
            return  # mute/deafen change etc. - not logged

        embed.add_field(name="User ID", value=str(member.id), inline=True)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceLogging(bot))

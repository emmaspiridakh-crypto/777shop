import datetime
import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.checks import staff_or_ownership_check, ownership_check
from utils.permissions import is_ceo


def parse_duration(duration: str) -> datetime.timedelta | None:
    """Parses a duration string like '10m', '1h', '2d' into a timedelta."""
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    try:
        unit = duration[-1].lower()
        amount = int(duration[:-1])
        if unit not in units or amount <= 0:
            return None
        return datetime.timedelta(**{units[unit]: amount})
    except (ValueError, IndexError):
        return None


async def _log_mod_action(bot: commands.Bot, *, channel_id: int, title: str, color: int,
                           moderator: discord.abc.User, target, reason: str, extra: dict | None = None):
    channel = bot.get_channel(channel_id)
    if channel is None:
        return

    embed = discord.Embed(title=title, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
    embed.add_field(name="Moderator", value=f"{moderator.mention} (`{moderator}` / `{moderator.id}`)", inline=False)

    if isinstance(target, (discord.Member, discord.User)):
        target_str = f"{target.mention} (`{target}` / `{target.id}`)"
        embed.set_thumbnail(url=target.display_avatar.url)
    else:
        target_str = f"`{target}`"

    embed.add_field(name="Target", value=target_str, inline=False)
    embed.add_field(name="Reason", value=reason or "Δεν δόθηκε λόγος", inline=False)

    if extra:
        for name, value in extra.items():
            embed.add_field(name=name, value=value, inline=True)

    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        pass


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- /kick ----------
    @app_commands.command(name="kick", description="Κάνει kick έναν χρήστη από τον server")
    @app_commands.describe(member="Ο χρήστης προς αποβολή", reason="Ο λόγος της αποβολής")
    @staff_or_ownership_check()
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Δεν δόθηκε λόγος"):
        if member.id == interaction.user.id:
            await interaction.response.send_message("🚫 Δεν μπορείς να κάνεις kick τον εαυτό σου.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("🚫 Δεν μπορείς να κάνεις kick αυτόν τον χρήστη (ίσος ή υψηλότερος ρόλος).", ephemeral=True)
            return

        try:
            await member.kick(reason=f"{reason} | Moderator: {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ Δεν έχω δικαίωμα να κάνω kick αυτόν τον χρήστη.", ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f"⚠️ Σφάλμα: {e}", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Ο/Η {member.mention} αποβλήθηκε. Λόγος: {reason}")
        await _log_mod_action(
            self.bot, channel_id=config.KICK_LOG_CHANNEL_ID, title="👢 Member Kicked",
            color=config.COLOR_WARNING, moderator=interaction.user, target=member, reason=reason,
        )

    # ---------- /timeout ----------
    @app_commands.command(name="timeout", description="Βάζει timeout σε έναν χρήστη")
    @app_commands.describe(member="Ο χρήστης", duration="Διάρκεια π.χ. 10m, 1h, 2d", reason="Ο λόγος")
    @staff_or_ownership_check()
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "Δεν δόθηκε λόγος"):
        if member.id == interaction.user.id:
            await interaction.response.send_message("🚫 Δεν μπορείς να βάλεις timeout στον εαυτό σου.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("🚫 Δεν μπορείς να βάλεις timeout σε αυτόν τον χρήστη (ίσος ή υψηλότερος ρόλος).", ephemeral=True)
            return

        delta = parse_duration(duration)
        if delta is None:
            await interaction.response.send_message(
                "⚠️ Μη έγκυρη διάρκεια. Χρησιμοποίησε π.χ. `10m`, `1h`, `2d` (max 28d).", ephemeral=True
            )
            return
        if delta > datetime.timedelta(days=28):
            await interaction.response.send_message("⚠️ Η μέγιστη διάρκεια timeout είναι 28 ημέρες.", ephemeral=True)
            return

        try:
            await member.timeout(delta, reason=f"{reason} | Moderator: {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ Δεν έχω δικαίωμα να κάνω timeout αυτόν τον χρήστη.", ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f"⚠️ Σφάλμα: {e}", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Ο/Η {member.mention} πήρε timeout για {duration}. Λόγος: {reason}")
        await _log_mod_action(
            self.bot, channel_id=config.TIMEOUT_LOG_CHANNEL_ID, title="⏱️ Member Timed Out",
            color=config.COLOR_WARNING, moderator=interaction.user, target=member, reason=reason,
            extra={"Duration": duration},
        )

    # ---------- /ban ----------
    @app_commands.command(name="ban", description="Κάνει ban έναν χρήστη")
    @app_commands.describe(member="Ο χρήστης προς ban", reason="Ο λόγος", delete_days="Διαγραφή μηνυμάτων (ημέρες, 0-7)")
    @staff_or_ownership_check()
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Δεν δόθηκε λόγος", delete_days: app_commands.Range[int, 0, 7] = 0):
        if member.id == interaction.user.id:
            await interaction.response.send_message("🚫 Δεν μπορείς να κάνεις ban τον εαυτό σου.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("🚫 Δεν μπορείς να κάνεις ban αυτόν τον χρήστη (ίσος ή υψηλότερος ρόλος).", ephemeral=True)
            return

        try:
            await member.ban(reason=f"{reason} | Moderator: {interaction.user}", delete_message_days=delete_days)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ Δεν έχω δικαίωμα να κάνω ban αυτόν τον χρήστη.", ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f"⚠️ Σφάλμα: {e}", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Ο/Η {member.mention} έφαγε ban. Λόγος: {reason}")
        await _log_mod_action(
            self.bot, channel_id=config.BAN_LOG_CHANNEL_ID, title="🔨 Member Banned",
            color=config.COLOR_DANGER, moderator=interaction.user, target=member, reason=reason,
        )

    # ---------- /unban ----------
    @app_commands.command(name="unban", description="Κάνει unban έναν χρήστη με το User ID του")
    @app_commands.describe(user_id="Το ID του χρήστη", reason="Ο λόγος")
    @staff_or_ownership_check()
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "Δεν δόθηκε λόγος"):
        try:
            uid = int(user_id)
        except ValueError:
            await interaction.response.send_message("⚠️ Μη έγκυρο User ID.", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(uid)
            await interaction.guild.unban(user, reason=f"{reason} | Moderator: {interaction.user}")
        except discord.NotFound:
            await interaction.response.send_message("⚠️ Ο χρήστης δεν βρέθηκε ή δεν είναι banned.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ Δεν έχω δικαίωμα να κάνω unban.", ephemeral=True)
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f"⚠️ Σφάλμα: {e}", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Ο/Η {user.mention} ξαναμπήκε (unban). Λόγος: {reason}")
        await _log_mod_action(
            self.bot, channel_id=config.BAN_LOG_CHANNEL_ID, title="🔓 Member Unbanned",
            color=config.COLOR_SUCCESS, moderator=interaction.user, target=user, reason=reason,
        )

    # ---------- /say (ownership only) ----------
    @app_commands.command(name="say", description="Ο bot στέλνει το μήνυμα που γράφεις (CEO/COO/CTO μόνο)")
    @app_commands.describe(message="Το μήνυμα προς αποστολή", channel="Το channel (προαιρετικό, default = εδώ)")
    @ownership_check()
    async def say(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        try:
            await target_channel.send(message)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"⚠️ Σφάλμα: {e}", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Στάλθηκε στο {target_channel.mention}.", ephemeral=True)

    # ---------- !dmall (CEO only, prefix command) ----------
    @commands.command(name="dmall")
    async def dmall(self, ctx: commands.Context, *, message: str = None):
        if not isinstance(ctx.author, discord.Member) or not is_ceo(ctx.author):
            await ctx.reply("🚫 Αυτή η εντολή είναι μόνο για τον CEO.", mention_author=False)
            return

        if not message:
            await ctx.reply("⚠️ Χρήση: `!dmall <μήνυμα>`", mention_author=False)
            return

        status_msg = await ctx.reply(f"📨 Στέλνω DM σε {ctx.guild.member_count} μέλη...", mention_author=False)

        sent, failed = 0, 0
        for member in ctx.guild.members:
            if member.bot:
                continue
            try:
                await member.send(message)
                sent += 1
            except discord.HTTPException:
                failed += 1

        await status_msg.edit(content=f"✅ Ολοκληρώθηκε. Στάλθηκαν: **{sent}** | Απέτυχαν: **{failed}**")

    # ---------- Error handling ----------
    @kick.error
    @timeout.error
    @ban.error
    @unban.error
    @say.error
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            msg = str(error) or "🚫 Δεν έχεις δικαίωμα να χρησιμοποιήσεις αυτή την εντολή."
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        else:
            if interaction.response.is_done():
                await interaction.followup.send(f"⚠️ Σφάλμα: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ Σφάλμα: {error}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))

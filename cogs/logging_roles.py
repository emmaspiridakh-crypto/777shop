import datetime
import discord
from discord.ext import commands

import config


class RoleLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- Server-level role changes ----------

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        channel = self.bot.get_channel(config.ROLES_LOG_CHANNEL_ID)
        if channel is None:
            return

        embed = discord.Embed(
            title="➕ Role Created",
            description=f"**{role.name}** ({role.mention})",
            color=config.COLOR_SUCCESS,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="Role ID", value=str(role.id), inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        channel = self.bot.get_channel(config.ROLES_LOG_CHANNEL_ID)
        if channel is None:
            return

        embed = discord.Embed(
            title="➖ Role Deleted",
            description=f"**{role.name}**",
            color=config.COLOR_DANGER,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="Role ID", value=str(role.id), inline=True)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        channel = self.bot.get_channel(config.ROLES_LOG_CHANNEL_ID)
        if channel is None:
            return

        changes = []
        if before.name != after.name:
            changes.append(f"**Όνομα:** `{before.name}` → `{after.name}`")
        if before.color != after.color:
            changes.append(f"**Χρώμα:** `{before.color}` → `{after.color}`")
        if before.permissions != after.permissions:
            changes.append("**Permissions:** Άλλαξαν")
        if before.hoist != after.hoist:
            changes.append(f"**Hoist:** `{before.hoist}` → `{after.hoist}`")
        if before.mentionable != after.mentionable:
            changes.append(f"**Mentionable:** `{before.mentionable}` → `{after.mentionable}`")

        if not changes:
            return

        embed = discord.Embed(
            title="🔧 Role Updated",
            description=f"**{after.name}** ({after.mention})\n\n" + "\n".join(changes),
            color=config.COLOR_WARNING,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="Role ID", value=str(after.id), inline=True)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    # ---------- Member role add/remove ----------

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        channel = self.bot.get_channel(config.ROLES_LOG_CHANNEL_ID)
        if channel is None:
            return

        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added = after_roles - before_roles
        removed = before_roles - after_roles

        if not added and not removed:
            return

        embed = discord.Embed(
            title="👤 Member Roles Updated",
            description=f"{after.mention} (`{after}`)",
            color=config.COLOR_INFO,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_thumbnail(url=after.display_avatar.url)

        if added:
            embed.add_field(
                name="➕ Προστέθηκαν",
                value=", ".join(r.mention for r in added),
                inline=False,
            )
        if removed:
            embed.add_field(
                name="➖ Αφαιρέθηκαν",
                value=", ".join(r.mention for r in removed),
                inline=False,
            )
        embed.add_field(name="User ID", value=str(after.id), inline=True)

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleLogging(bot))

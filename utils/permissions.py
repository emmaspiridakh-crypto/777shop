import discord
import config


def _member_role_ids(member: discord.Member) -> set[int]:
    return {role.id for role in member.roles}


def is_staff_or_ownership(member: discord.Member) -> bool:
    """Staff, Manager, CEO, COO, CTO -> can see tickets, use kick/timeout/ban/unban."""
    if member.guild_permissions.administrator:
        return True
    ids = _member_role_ids(member)
    return any(rid in ids for rid in config.STAFF_AND_OWNERSHIP_ROLE_IDS if rid)


def is_ownership(member: discord.Member) -> bool:
    """CEO, COO, CTO only -> /say command."""
    if member.guild_permissions.administrator:
        return True
    ids = _member_role_ids(member)
    return any(rid in ids for rid in config.OWNERSHIP_ROLE_IDS if rid)


def is_ceo(member: discord.Member) -> bool:
    """CEO only -> !dmall command."""
    if member.guild_permissions.administrator:
        return True
    ids = _member_role_ids(member)
    return config.CEO_ROLE_ID in ids if config.CEO_ROLE_ID else False

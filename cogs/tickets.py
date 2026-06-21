import datetime
import discord
from discord import app_commands
from discord.ext import commands

import config
from utils import ticket_storage as storage
from utils.permissions import is_staff_or_ownership


def _ticket_overwrites(guild: discord.Guild, owner: discord.Member) -> dict:
    """Build permission overwrites: hidden from everyone, visible to owner + staff/ownership roles."""
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        owner: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
        ),
    }
    for role_id in config.STAFF_AND_OWNERSHIP_ROLE_IDS:
        if not role_id:
            continue
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True,
            )
    return overwrites


async def _send_ticket_log(bot: commands.Bot, *, action: str, ticket_type: str, channel: discord.abc.GuildChannel,
                            owner: discord.abc.User, closed_by: discord.abc.User | None = None,
                            ticket_number: int | None = None):
    log_channel = bot.get_channel(config.TICKET_LOG_CHANNEL_ID)
    if log_channel is None:
        return

    color = config.COLOR_SUCCESS if action == "Opened" else config.COLOR_DANGER
    embed = discord.Embed(
        title=f"🎫 Ticket {action}",
        color=color,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    embed.add_field(name="Type", value=ticket_type.capitalize(), inline=True)
    if ticket_number is not None:
        embed.add_field(name="Number", value=f"#{ticket_number:04d}", inline=True)
    embed.add_field(name="Channel", value=f"{channel.mention} (`{channel.name}`)", inline=False)
    embed.add_field(name="Owner", value=f"{owner.mention} (`{owner.id}`)", inline=True)
    if closed_by is not None:
        embed.add_field(name="Closed by", value=f"{closed_by.mention} (`{closed_by.id}`)", inline=True)

    try:
        await log_channel.send(embed=embed)
    except discord.HTTPException:
        pass


class TicketControlView(discord.ui.LayoutView):
    """Persistent view shown INSIDE an open ticket channel. Close + Ping User buttons."""

    def __init__(self):
        super().__init__(timeout=None)

        container = discord.ui.Container(accent_color=config.COLOR_INFO)

        section = discord.ui.Section(
            "## 🎫 Ticket Controls",
            "Χρησιμοποίησε τα κουμπιά παρακάτω για να διαχειριστείς αυτό το ticket.",
            accessory=discord.ui.Thumbnail(config.SUPPORT_THUMBNAIL_URL or "https://i.imgur.com/9sDnoUW.jpeg"),
        )
        container.add_item(section)

        row = discord.ui.ActionRow()

        close_btn = discord.ui.Button(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id="ticket:close",
        )
        close_btn.callback = self._on_close
        row.add_item(close_btn)

        ping_btn = discord.ui.Button(
            label="Ping User",
            style=discord.ButtonStyle.secondary,
            emoji="🔔",
            custom_id="ticket:ping_user",
        )
        ping_btn.callback = self._on_ping
        row.add_item(ping_btn)

        container.add_item(row)
        self.add_item(container)

    async def _on_close(self, interaction: discord.Interaction):
        await handle_close_ticket(interaction)

    async def _on_ping(self, interaction: discord.Interaction):
        await handle_ping_user(interaction)


async def handle_close_ticket(interaction: discord.Interaction):
    bot = interaction.client
    channel = interaction.channel
    ticket = storage.get_ticket(channel.id)

    if ticket is None:
        await interaction.response.send_message(
            "⚠️ Αυτό το channel δεν αναγνωρίζεται ως ενεργό ticket.", ephemeral=True
        )
        return

    owner_id = ticket["owner_id"]

    # Owner cannot close their own ticket
    if interaction.user.id == owner_id:
        await interaction.response.send_message(
            "🚫 Δεν μπορείς να κλείσεις εσύ το δικό σου ticket. Περίμενε το staff.", ephemeral=True
        )
        return

    await interaction.response.send_message("🔒 Το ticket κλείνει σε 5 δευτερόλεπτα...", ephemeral=False)

    storage.mark_closed(channel.id)

    owner = interaction.guild.get_member(owner_id)
    owner_obj = owner or discord.Object(id=owner_id)

    await _send_ticket_log(
        bot,
        action="Closed",
        ticket_type=ticket["ticket_type"],
        channel=channel,
        owner=owner if owner else await bot.fetch_user(owner_id),
        closed_by=interaction.user,
        ticket_number=ticket["ticket_number"],
    )

    storage.delete_ticket(channel.id)

    await discord.utils.sleep_until(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=5)
    )
    try:
        await channel.delete(reason=f"Ticket closed by {interaction.user}")
    except discord.HTTPException:
        pass


async def handle_ping_user(interaction: discord.Interaction):
    channel = interaction.channel
    ticket = storage.get_ticket(channel.id)

    if ticket is None:
        await interaction.response.send_message(
            "⚠️ Αυτό το channel δεν αναγνωρίζεται ως ενεργό ticket.", ephemeral=True
        )
        return

    owner_id = ticket["owner_id"]

    # The ticket owner cannot ping themselves
    if interaction.user.id == owner_id:
        await interaction.response.send_message(
            "🚫 Δεν μπορείς να κάνεις ping τον εαυτό σου.", ephemeral=True
        )
        return

    await interaction.response.send_message(f"<@{owner_id}> 🔔 Σε χρειάζονται εδώ!")


class TicketOpenButton(discord.ui.Button):
    def __init__(self, *, ticket_type: str, label: str, category_id: int, thumbnail_url: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            emoji="🎫",
            custom_id=f"ticket_panel:open:{ticket_type}",
        )
        self.ticket_type = ticket_type
        self.category_id = category_id
        self.thumbnail_url = thumbnail_url
        self.panel_label = label

    async def callback(self, interaction: discord.Interaction):
        await open_ticket(
            interaction,
            ticket_type=self.ticket_type,
            category_id=self.category_id,
            thumbnail_url=self.thumbnail_url,
            panel_label=self.panel_label,
        )


async def open_ticket(interaction: discord.Interaction, *, ticket_type: str, category_id: int,
                       thumbnail_url: str, panel_label: str):
    guild = interaction.guild
    user = interaction.user

    await interaction.response.defer(ephemeral=True)

    category = guild.get_channel(category_id)
    if category is None or not isinstance(category, discord.CategoryChannel):
        await interaction.followup.send(
            "⚠️ Η κατηγορία για αυτό το ticket δεν βρέθηκε.", ephemeral=True
        )
        return

    ticket_number = storage.next_ticket_number(ticket_type)
    channel_name = f"{ticket_type}-{ticket_number:04d}"

    overwrites = _ticket_overwrites(guild, user)

    try:
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"{panel_label} ticket opened by {user}",
        )
    except discord.HTTPException as e:
        await interaction.followup.send(f"⚠️ Αποτυχία δημιουργίας ticket: {e}", ephemeral=True)
        return

    storage.create_ticket(
        channel_id=channel.id,
        guild_id=guild.id,
        owner_id=user.id,
        ticket_type=ticket_type,
        ticket_number=ticket_number,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    control_view = TicketControlView()
    await channel.send(content=f"{user.mention}", view=control_view)

    await _send_ticket_log(
        interaction.client,
        action="Opened",
        ticket_type=ticket_type,
        channel=channel,
        owner=user,
        ticket_number=ticket_number,
    )

    await interaction.followup.send(f"✅ Το ticket σου δημιουργήθηκε: {channel.mention}", ephemeral=True)


class SupportPanelView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=config.COLOR_INFO)

        section = discord.ui.Section(
            "## 🛟 Support",
            "Χρειάζεσαι βοήθεια; Πάτησε το κουμπί παρακάτω για να ανοίξεις ένα ticket "
            "και η ομάδα μας θα σε εξυπηρετήσει το συντομότερο δυνατό.",
            accessory=discord.ui.Thumbnail(config.SUPPORT_THUMBNAIL_URL or "https://i.imgur.com/9sDnoUW.jpeg"),
        )
        container.add_item(section)

        row = discord.ui.ActionRow()
        row.add_item(
            TicketOpenButton(
                ticket_type="support",
                label="Support",
                category_id=config.SUPPORT_CATEGORY_ID,
                thumbnail_url=config.SUPPORT_THUMBNAIL_URL,
            )
        )
        container.add_item(row)
        self.add_item(container)


class OrderPanelView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=config.COLOR_WARNING)

        section = discord.ui.Section(
            "## 🛒 Order",
            "Θέλεις να κάνεις παραγγελία; Πάτησε το κουμπί παρακάτω για να ανοίξεις ένα ticket "
            "και η ομάδα μας θα αναλάβει την παραγγελία σου.",
            accessory=discord.ui.Thumbnail(config.ORDER_THUMBNAIL_URL or "https://i.imgur.com/9sDnoUW.jpeg"),
        )
        container.add_item(section)

        row = discord.ui.ActionRow()
        row.add_item(
            TicketOpenButton(
                ticket_type="order",
                label="Order",
                category_id=config.ORDER_CATEGORY_ID,
                thumbnail_url=config.ORDER_THUMBNAIL_URL,
            )
        )
        container.add_item(row)
        self.add_item(container)


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        storage.init_db()
        # Register persistent views so buttons survive restarts
        self.bot.add_view(SupportPanelView())
        self.bot.add_view(OrderPanelView())
        self.bot.add_view(TicketControlView())

    group = app_commands.Group(name="ticketpanel", description="Διαχείριση ticket panels")

    @group.command(name="support", description="Στέλνει το Support ticket panel σε αυτό το channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def support_panel(self, interaction: discord.Interaction):
        await interaction.channel.send(view=SupportPanelView())
        await interaction.response.send_message("✅ Στάλθηκε το Support panel.", ephemeral=True)

    @group.command(name="order", description="Στέλνει το Order ticket panel σε αυτό το channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def order_panel(self, interaction: discord.Interaction):
        await interaction.channel.send(view=OrderPanelView())
        await interaction.response.send_message("✅ Στάλθηκε το Order panel.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))

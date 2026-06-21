import os
from dotenv import load_dotenv

load_dotenv()


def _int(name: str) -> int:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return 0
    try:
        return int(val)
    except ValueError:
        return 0


# ---------- Bot ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------- Roles ----------
STAFF_ROLE_ID = _int("STAFF_ROLE_ID")
MANAGER_ROLE_ID = _int("MANAGER_ROLE_ID")
CEO_ROLE_ID = _int("CEO_ROLE_ID")
COO_ROLE_ID = _int("COO_ROLE_ID")
CTO_ROLE_ID = _int("CTO_ROLE_ID")

# Roles that can see tickets + use kick/timeout/ban/unban
STAFF_AND_OWNERSHIP_ROLE_IDS = [
    STAFF_ROLE_ID,
    MANAGER_ROLE_ID,
    CEO_ROLE_ID,
    COO_ROLE_ID,
    CTO_ROLE_ID,
]

# Roles that can use /say
OWNERSHIP_ROLE_IDS = [CEO_ROLE_ID, COO_ROLE_ID, CTO_ROLE_ID]

# Role automatically given to new members on join
AUTOROLE_ID = _int("AUTOROLE_ID")

# ---------- Ticket System: Support ----------
SUPPORT_CATEGORY_ID = _int("SUPPORT_CATEGORY_ID")
SUPPORT_PANEL_CHANNEL_ID = _int("SUPPORT_PANEL_CHANNEL_ID")
SUPPORT_THUMBNAIL_URL = os.getenv("SUPPORT_THUMBNAIL_URL", "")

# ---------- Ticket System: Order ----------
ORDER_CATEGORY_ID = _int("ORDER_CATEGORY_ID")
ORDER_PANEL_CHANNEL_ID = _int("ORDER_PANEL_CHANNEL_ID")
ORDER_THUMBNAIL_URL = os.getenv("ORDER_THUMBNAIL_URL", "")

# ---------- Ticket Logs ----------
TICKET_LOG_CHANNEL_ID = _int("TICKET_LOG_CHANNEL_ID")

# ---------- Logging Channels ----------
JOIN_LEAVE_LOG_CHANNEL_ID = _int("JOIN_LEAVE_LOG_CHANNEL_ID")
VOICE_LOG_CHANNEL_ID = _int("VOICE_LOG_CHANNEL_ID")
MESSAGE_LOG_CHANNEL_ID = _int("MESSAGE_LOG_CHANNEL_ID")
CHANNEL_LOG_CHANNEL_ID = _int("CHANNEL_LOG_CHANNEL_ID")
ROLES_LOG_CHANNEL_ID = _int("ROLES_LOG_CHANNEL_ID")
KICK_LOG_CHANNEL_ID = _int("KICK_LOG_CHANNEL_ID")
TIMEOUT_LOG_CHANNEL_ID = _int("TIMEOUT_LOG_CHANNEL_ID")
BAN_LOG_CHANNEL_ID = _int("BAN_LOG_CHANNEL_ID")

# ---------- Web server ----------
PORT = _int("PORT") or 10000

# ---------- Colors ----------
COLOR_DEFAULT = 0x2B2D31
COLOR_SUCCESS = 0x57F287
COLOR_DANGER = 0xED4245
COLOR_WARNING = 0xFEE75C
COLOR_INFO = 0x5865F2

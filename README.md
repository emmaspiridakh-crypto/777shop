# Ticket & Logging Bot

## 📁 Τι περιέχει

### 🎫 Ticket System (Components V2)
- **Support Panel** → button "Support" → ανοίγει channel στο `SUPPORT_CATEGORY_ID`
- **Order Panel** → button "Order" → ανοίγει channel στο `ORDER_CATEGORY_ID`
- Κάθε ticket channel είναι ορατό μόνο στον owner + Staff/Manager/CEO/COO/CTO
- Μέσα στο ticket: panel με thumbnail + 2 buttons:
  - **Close Ticket** → όλοι ΕΚΤΟΣ από τον owner μπορούν να το κλείσουν (διαγράφεται το channel μετά από 5 δευτ.)
  - **Ping User** → κάνει ping τον owner· ο ίδιος ο owner δεν μπορεί να το πατήσει
- Persistent views: τα buttons δουλεύουν ακόμα και μετά από restart του bot
- Ξεχωριστή αρίθμηση tickets ανά τύπο (`support-0001`, `order-0001`, ...)
- Log όταν ανοίγει/κλείνει ticket → `TICKET_LOG_CHANNEL_ID`

**Πώς στέλνεις τα panels:** χρησιμοποίησε τα slash commands (χρειάζονται Administrator):
- `/ticketpanel support` → στέλνει το Support panel στο τρέχον channel
- `/ticketpanel order` → στέλνει το Order panel στο τρέχον channel

### 📋 Logging (6 ξεχωριστά channels + ticket logs)
| Τύπος | Env Variable |
|---|---|
| Join/Leave | `JOIN_LEAVE_LOG_CHANNEL_ID` |
| Voice (join/leave/move) | `VOICE_LOG_CHANNEL_ID` |
| Messages (edit/delete) | `MESSAGE_LOG_CHANNEL_ID` |
| Channels (create/delete/edit) | `CHANNEL_LOG_CHANNEL_ID` |
| Roles (server roles + member role add/remove) | `ROLES_LOG_CHANNEL_ID` |
| Kick | `KICK_LOG_CHANNEL_ID` |
| Timeout | `TIMEOUT_LOG_CHANNEL_ID` |
| Ban/Unban (μαζί) | `BAN_LOG_CHANNEL_ID` |
| Ticket open/close | `TICKET_LOG_CHANNEL_ID` |

Όλα τα moderation logs δείχνουν **moderator + target + reason + timestamp**.

### 🛡️ Moderation Commands
| Command | Ποιος μπορεί |
|---|---|
| `/kick` | Staff, Manager, CEO, COO, CTO |
| `/timeout` | Staff, Manager, CEO, COO, CTO |
| `/ban` | Staff, Manager, CEO, COO, CTO |
| `/unban` | Staff, Manager, CEO, COO, CTO |
| `/say` | Μόνο CEO, COO, CTO |
| `!dmall <μήνυμα>` | Μόνο CEO |

> Υπάρχει επίσης role-hierarchy check (δεν μπορείς να κάνεις kick/timeout/ban κάποιον με ίσο ή υψηλότερο ρόλο από σένα, εκτός αν είσαι ο owner του server).

### 🎭 Autorole
Όταν μπαίνει νέο μέλος (όχι bot), παίρνει αυτόματα τον ρόλο `AUTOROLE_ID`. Αν δεν οριστεί, η λειτουργία είναι απενεργοποιημένη.

---

## ⚙️ Ρύθμιση (.env)

Αντίγραψε το `.env.example` σε `.env` και συμπλήρωσε:

1. **BOT_TOKEN** — από το Discord Developer Portal
2. **Role IDs** — `STAFF_ROLE_ID`, `MANAGER_ROLE_ID`, `CEO_ROLE_ID`, `COO_ROLE_ID`, `CTO_ROLE_ID`
   - Discord → Settings → Advanced → Developer Mode (ON) → δεξί κλικ σε ρόλο → Copy Role ID
3. **Category IDs** — `SUPPORT_CATEGORY_ID`, `ORDER_CATEGORY_ID` (οι categories όπου θα ανοίγουν τα tickets)
4. **Thumbnail URLs** — `SUPPORT_THUMBNAIL_URL`, `ORDER_THUMBNAIL_URL` (direct image link, π.χ. από imgur)
5. **Όλα τα log channel IDs**

### Discord Developer Portal — Privileged Intents
Χρειάζεται να ενεργοποιήσεις (Bot tab):
- ✅ SERVER MEMBERS INTENT
- ✅ MESSAGE CONTENT INTENT

### Bot Permissions (κατά το invite)
Χρειάζεται τουλάχιστον: `Manage Channels`, `Manage Roles`, `Kick Members`, `Ban Members`, `Moderate Members` (timeout), `Send Messages`, `Embed Links`, `Read Message History`, `View Channels`.

⚠️ **Σημαντικό:** Ο ρόλος του bot πρέπει να είναι **πάνω** από τους ρόλους Staff/Manager στο role hierarchy, αλλιώς δε θα μπορεί να βάλει permission overwrites σωστά σε όλους.

---

## 🚀 Local testing
```bash
pip install -r requirements.txt --break-system-packages
python main.py
```

## 🐳 Render Deployment
1. Push το repo στο GitHub
2. Render → New → Web Service → Docker
3. Πρόσθεσε ΟΛΑ τα environment variables από το `.env.example` στο Render dashboard
4. Deploy — το Flask server (`keep_alive.py`) κρατάει το service ζωντανό στο PORT

---

## 🗂️ Δομή project
```
ticketbot/
├── main.py                  # Entry point
├── config.py                 # Διαβάζει .env
├── keep_alive.py             # Flask web server
├── requirements.txt
├── Dockerfile
├── .env.example
├── cogs/
│   ├── tickets.py             # Ticket system (Components V2)
│   ├── autorole.py             # Autorole on join
│   ├── logging_member.py      # Join/Leave
│   ├── logging_voice.py       # Voice
│   ├── logging_messages.py    # Message edit/delete
│   ├── logging_channels.py    # Channel create/delete/edit
│   ├── logging_roles.py       # Role logs
│   └── moderation.py          # kick/timeout/ban/unban/say/dmall
├── utils/
│   ├── permissions.py         # Έλεγχοι ρόλων
│   ├── checks.py               # app_commands checks
│   └── ticket_storage.py       # SQLite
└── data/
    └── tickets.db              # Δημιουργείται αυτόματα
```

## 📝 Σημειώσεις
- Το SQLite db (`data/tickets.db`) είναι **ephemeral** στο Render (δεν διατηρείται σε redeploy εκτός αν προσθέσεις persistent disk). Αν θες μόνιμη αποθήκευση ιστορικού tickets, πες μου να προσθέσω Render Persistent Disk ή external DB.
- Αν θες τα panels να στέλνονται **αυτόματα** στο startup αντί για slash command, πες μου να το αλλάξω.

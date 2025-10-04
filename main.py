# main.py
# Single-file Discord bot with multiple features/games.
# Requires:
#   pip install -U discord.py aiohttp

# ============================================================
# ===============  CORE IMPORTS & INITIALIZATION  ============
# ============================================================

import os
import re
import hmac
import json
import base64
import hashlib
import random
import math
import time
import asyncio
from typing import Optional, List, Dict, Set, Tuple

import aiohttp
import discord
from discord import app_commands

# ---- Tokens (from your existing file) ----
from dis_token import Enigma, TOD, Thinker  # you can switch the one you run
TOKEN = Enigma  # change here if needed

# ---- Discord client / intents ----
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ---- Paths to existing files ----
TRUTH_PATH = os.path.join("truth_or_dare", "truth_file.txt")
DARE_PATH  = os.path.join("truth_or_dare", "dare_file.txt")
RICE_PATH  = os.path.join("rice_purity_test", "rice_purity_questions.txt")
TRIVIA_PATH = os.path.join("trivia", "trivia_questions.json")


# ============================================================
# ===================  SHARED UTILITIES  =====================
# ============================================================

def load_lines(path: str) -> List[str]:
    """Load non-empty, stripped lines from a UTF-8 file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return []

def load_trivia_local(path: str) -> List[Dict]:
    """
    Load trivia from JSON:
    [
      {"question": "Q?", "choices": ["A","B","C","D"], "answer": 0}
    ]
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        good = []
        for item in data:
            if (
                isinstance(item, dict)
                and isinstance(item.get("question"), str)
                and isinstance(item.get("choices"), list)
                and len(item["choices"]) == 4
                and all(isinstance(c, str) for c in item["choices"])
                and isinstance(item.get("answer"), int)
                and 0 <= item["answer"] < 4
            ):
                good.append(item)
        return good
    except FileNotFoundError:
        return []
    except Exception:
        return []

TRUTH_QUESTIONS = load_lines(TRUTH_PATH)
DARE_QUESTIONS  = load_lines(DARE_PATH)
RICE_QUESTIONS  = load_lines(RICE_PATH)
TRIVIA_FALLBACK = load_trivia_local(TRIVIA_PATH)

def make_embed(title: str, desc: str = "", color: discord.Color = discord.Color.blurple()):
    return discord.Embed(title=title, description=desc, color=color)


# ============================================================
# ===================  BASIC / META CMDS  ====================
# ============================================================

@tree.command(name="ping", description="Check bot latency.")
async def ping_cmd(inter: discord.Interaction):
    await inter.response.send_message(f"Pong! {round(client.latency * 1000)} ms", ephemeral=True)

@tree.command(name="help", description="Show all commands & features.")
async def help_cmd(inter: discord.Interaction):
    desc = (
        "**Encryption**\n"
        "• `/encrypt seed:<text> message:<text> [hidden:false]` – Encrypt (Base64), **public by default**, "
        "posts a single embed that shows your name+avatar and has a **Decrypt** button\n"
        "• `/decrypt seed:<text> message:<base64> [hidden:true]` – Decrypt (hidden by default)\n\n"

        "**Morse**\n"
        "• `/morse-encrypt message:<text>`\n"
        "• `/morse-decrypt code:<morse>`\n\n"

        "**Clone (Webhook)**\n"
        "• `/clone target_user:<member> message:<text>` – Send via webhook as that display name (needs Manage Webhooks)\n"
        "• `/clone-embed target_user:<member> title:<text> [description] [color HEX]`\n\n"

        "**Moderation (needs proper perms)**\n"
        "• `/server-mute` `/server-unmute` `/server-deafen` `/server-undeafen`\n"
        "• `/disconnect-voice` `/move-voice` `/change-nickname` `/print-bot-permissions`\n"
        "• `/court user:<member> seconds:<int>` – Adds 'Jail' role for X seconds (auto-removes)\n\n"

        "**Truth or Dare & Tests**\n"
        "• `/truth` • `/dare` – from your files in truth_or_dare/\n"
        "• `/ricepurity [anonymous:<true|false>]` – interactive test using rice_purity_test file\n\n"

        "**Mini-Games**\n"
        "• `/coinflip` • `/roll dice:<e.g. 2d6+1>`\n"
        "• `/rps [opponent:@user]` – free join or challenge, private picks, rematch & score (victory embed)\n"
        "• `/trivia [questions:<1-50>] [timer:<5-60>]` – Kahoot-style: timer, everyone answers, speed points, API-backed\n"
        "• `/tictactoe opponent:<member>` – X/O board game (victory embed)\n\n"

        "**Misc**\n"
        "• `/who-am-i` – Your display name"
    )
    await inter.response.send_message(embed=make_embed("Mega Bot – Commands", desc), ephemeral=True)

@tree.command(name="who-am-i", description="Your display name.")
async def who_am_i(inter: discord.Interaction):
    await inter.response.send_message(inter.user.display_name, ephemeral=True)


# ============================================================
# =====================  ENIGMA (NEW)  =======================
# ========== Strong seed-based symmetric encryption ==========
# ============================================================

def _derive_block(seed: str, counter: int) -> bytes:
    key = seed.encode("utf-8")
    msg = f"blk:{counter}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).digest()

def _keystream(seed: str, nbytes: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < nbytes:
        out.extend(_derive_block(seed, counter))
        counter += 1
    return bytes(out[:nbytes])

def strong_encrypt(plaintext: str, seed: str) -> str:
    data = plaintext.encode("utf-8")
    ks = _keystream(seed, len(data))
    ct = bytes([a ^ b for a, b in zip(data, ks)])
    return base64.urlsafe_b64encode(ct).decode("ascii")

def strong_decrypt(cipher_b64: str, seed: str) -> str:
    ct = base64.urlsafe_b64decode(cipher_b64.encode("ascii"))
    ks = _keystream(seed, len(ct))
    pt = bytes([a ^ b for a, b in zip(ct, ks)])
    return pt.decode("utf-8", errors="replace")

# ------- Decrypt UI (Modal + Button) -------

class DecryptModal(discord.ui.Modal, title="Decrypt Message"):
    seed: discord.ui.TextInput = discord.ui.TextInput(
        label="Seed / Key",
        placeholder="Enter the exact seed you used to encrypt",
        style=discord.TextStyle.short,
        required=True,
        max_length=200,
    )

    def __init__(self, ciphertext: str):
        super().__init__()
        self.ciphertext = ciphertext

    async def on_submit(self, interaction: discord.Interaction):
        try:
            plaintext = strong_decrypt(self.ciphertext, str(self.seed))
            await interaction.response.send_message(
                f":unlock: **Decrypted:** {plaintext}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Decryption failed: `{e}`",
                ephemeral=True
            )

class DecryptView(discord.ui.View):
    def __init__(self, ciphertext: str):
        super().__init__(timeout=600.0)
        self.ciphertext = ciphertext

    @discord.ui.button(label="Decrypt", style=discord.ButtonStyle.primary)
    async def decrypt_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DecryptModal(self.ciphertext))

# ------- Commands -------

@tree.command(name="encrypt", description="Encrypt text (Base64 output) and post a single embed with a Decrypt button.")
@app_commands.describe(hidden="If true, only the initial ack is hidden (default: False). The encrypted message itself is public.")
async def encrypt_cmd(inter: discord.Interaction, seed: str, message: str, hidden: Optional[bool] = False):
    await inter.response.defer(ephemeral=bool(hidden))
    try:
        ciphertext = strong_encrypt(message, seed)
        avatar_url = inter.user.display_avatar.url
        emb = discord.Embed(
            # description=f":lock: `{ciphertext}`\n\n🔐 Need to read it? Click **Decrypt** and enter the seed.",
            description=f":lock: `{ciphertext}`",
            color=discord.Color.blurple()
        )
        emb.set_author(name=inter.user.display_name, icon_url=avatar_url)
        # emb.set_footer(text="Decrypt opens a private modal; result is sent ephemerally to you.")
        view = DecryptView(ciphertext)
        await inter.followup.send(embed=emb, view=view, ephemeral=False)
    except Exception as e:
        await inter.followup.send(f"Error during encryption: {e}", ephemeral=True)

@tree.command(name="decrypt", description="Decrypt text (Base64 input).")
@app_commands.describe(hidden="If true, only you see the result (default: True)")
async def decrypt_cmd(inter: discord.Interaction, seed: str, message: str, hidden: Optional[bool] = True):
    try:
        out = strong_decrypt(message, seed)
        await inter.response.send_message(f":unlock: {out}", ephemeral=bool(hidden))
    except Exception as e:
        await inter.response.send_message(f"Error: {e}", ephemeral=bool(hidden))


# ============================================================
# ========================  MORSE  ===========================
# ============================================================

MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',  'E': '.',   'F': '..-.',
    'G': '--.','H': '....','I': '..',   'J': '.---', 'K': '-.-',  'L': '.-..',
    'M': '--', 'N': '-.',  'O': '---',  'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-',  'U': '..-',  'V': '...-', 'W': '.--',  'X': '-..-',
    'Y': '-.--','Z': '--..',
    '1': '.----','2': '..---','3': '...--','4': '....-','5': '.....',
    '6': '-....','7': '--...','8': '---..','9': '----.','0': '-----',
    ',': '--..--','.' : '.-.-.-','?':'..--..','/':'-..-.','-':'-....-',
    '(': '-.--.', ')':'-.--.-', '!':'-.-.--', ':':'---...',';':'-.-.-.',
    "'":'.----.','@':'.--.-.','&':'.-...','=':'-...-','+':'.-.-.',
    '_':'..--.-','"':'.-..-.','$':'...-..-', ' ':'/'
}
REV_MORSE = {v.strip(): k for k, v in MORSE_CODE.items()}

def morse_encrypt(msg: str) -> str:
    out = []
    for ch in msg.upper():
        out.append(MORSE_CODE.get(ch, '?'))
    return ' '.join(out)

def morse_decrypt(code: str) -> str:
    tokens = code.replace('   ', ' / ').split(' ')
    out = []
    for t in tokens:
        if not t:
            continue
        if t == '/':
            out.append(' ')
        else:
            out.append(REV_MORSE.get(t, '�'))
    return ''.join(out)

@tree.command(name="morse-encrypt", description="Convert text to Morse.")
async def morse_enc_cmd(inter: discord.Interaction, message: str):
    await inter.response.send_message(morse_encrypt(message), ephemeral=False)

@tree.command(name="morse-decrypt", description="Convert Morse to text.")
async def morse_dec_cmd(inter: discord.Interaction, code: str):
    await inter.response.send_message(morse_decrypt(code), ephemeral=True)


# ============================================================
# =====================  CLONE (WEBHOOK)  ====================
# ============================================================

@tree.command(name="clone", description="Clone a user's display name and send a message via webhook (requires Manage Webhooks).")
async def clone_cmd(inter: discord.Interaction, target_user: discord.Member, message: str):
    try:
        webhook = await inter.channel.create_webhook(name=target_user.display_name)
        avatar_url = target_user.display_avatar.url
        await webhook.send(content=message, username=target_user.display_name, avatar_url=avatar_url)
        await webhook.delete()
        await inter.response.send_message("Message sent via webhook.", ephemeral=True)
    except discord.Forbidden:
        await inter.response.send_message("Missing permission to manage webhooks here.", ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Error: {e}", ephemeral=True)

@tree.command(name="clone-embed", description="Clone a user's display name and send an embed via webhook (requires Manage Webhooks).")
async def clone_embed_cmd(inter: discord.Interaction, target_user: discord.Member, title: str, description: str = "", color: Optional[str] = None):
    webhook = None
    try:
        webhook = await inter.channel.create_webhook(name=target_user.display_name)
        avatar_url = target_user.display_avatar.url
        color_val = int(color, 16) if color and re.match(r'^[0-9a-fA-F]{6}$', color) else 0x3498db
        embed = discord.Embed(title=title, description=description, color=color_val)
        embed.set_author(name=target_user.display_name, icon_url=avatar_url)
        await webhook.send(embed=embed, username=target_user.display_name, avatar_url=avatar_url)
        await inter.response.send_message("Embed sent via webhook.", ephemeral=True)
    except discord.Forbidden:
        await inter.response.send_message("Missing permission to manage webhooks here.", ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Error: {e}", ephemeral=True)
    finally:
        if webhook:
            try: await webhook.delete()
            except Exception: pass


# ============================================================
# ======================  MODERATION  ========================
# =========== (NO give-role function as requested) ===========
# ============================================================

@tree.command(name="server-mute", description="Server mute a user.")
async def server_mute(inter: discord.Interaction, target_user: discord.Member):
    await target_user.edit(mute=True)
    await inter.response.send_message(f"{target_user.mention} has been server muted.", ephemeral=True)

@tree.command(name="server-unmute", description="Server unmute a user.")
async def server_unmute(inter: discord.Interaction, target_user: discord.Member):
    await target_user.edit(mute=False)
    await inter.response.send_message(f"{target_user.mention} has been server unmuted.", ephemeral=True)

@tree.command(name="server-deafen", description="Server deafen a user.")
async def server_deafen(inter: discord.Interaction, target_user: discord.Member):
    await target_user.edit(deafen=True)
    await inter.response.send_message(f"{target_user.mention} has been server deafened.", ephemeral=True)

@tree.command(name="server-undeafen", description="Server undeafen a user.")
async def server_undeafen(inter: discord.Interaction, target_user: discord.Member):
    await target_user.edit(deafen=False)
    await inter.response.send_message(f"{target_user.mention} has been server undeafened.", ephemeral=True)

@tree.command(name="disconnect-voice", description="Disconnect a user from voice.")
async def disconnect_voice(inter: discord.Interaction, target_user: discord.Member):
    await target_user.edit(voice_channel=None)
    await inter.response.send_message(f"{target_user.mention} has been disconnected.", ephemeral=True)

@tree.command(name="move-voice", description="Move a user to a target voice channel.")
async def move_voice(inter: discord.Interaction, target_user: discord.Member, target_channel: discord.VoiceChannel):
    await target_user.edit(voice_channel=target_channel)
    await inter.response.send_message(f"{target_user.mention} moved to {target_channel.mention}.", ephemeral=True)

@tree.command(name="change-nickname", description="Change a user's server nickname.")
async def change_nick(inter: discord.Interaction, target_user: discord.Member, new_nickname: str):
    await target_user.edit(nick=new_nickname)
    await inter.response.send_message(f"{target_user.mention} nickname changed to **{new_nickname}**.", ephemeral=True)

@tree.command(name="print-bot-permissions", description="Print bot guild permissions.")
async def print_perms(inter: discord.Interaction):
    await inter.response.send_message(f"Bot permissions: `{inter.guild.me.guild_permissions}`", ephemeral=True)

@tree.command(name="court", description="Give 'Jail' role to a user for X seconds, then remove it.")
async def court_cmd(inter: discord.Interaction, user: discord.Member, seconds: app_commands.Range[int, 1, 86400]):
    role = discord.utils.get(inter.guild.roles, name="Jail")
    if not role:
        await inter.response.send_message("Role 'Jail' not found.", ephemeral=True)
        return
    await user.add_roles(role, reason=f"Court by {inter.user} for {seconds}s")
    await inter.response.send_message(f"Sending {user.mention} to court for {seconds} seconds.", ephemeral=True)
    await asyncio.sleep(seconds)
    try:
        await user.remove_roles(role, reason="Court time elapsed")
    except Exception:
        pass


# ============================================================
# ====================  TRUTH OR DARE  =======================
# ============================================================

class TruthOrDareView(discord.ui.View):
    def __init__(self, inter: discord.Interaction):
        super().__init__(timeout=180.0)
        self.inter = inter
        self.kind: Optional[str] = None
        self.msg: Optional[discord.Message] = None

    def _pick(self) -> str:
        if self.kind == "truth":
            return random.choice(TRUTH_QUESTIONS) if TRUTH_QUESTIONS else "No truths found."
        return random.choice(DARE_QUESTIONS) if DARE_QUESTIONS else "No dares found."

    def _embed(self, text: str) -> discord.Embed:
        c = discord.Color.green() if self.kind == "truth" else discord.Color.red()
        e = discord.Embed(title=f"Random {self.kind.title()}", description=text, color=c)
        e.set_author(name=f"Requested by {self.inter.user.display_name}", icon_url=self.inter.user.display_avatar.url)
        return e

    async def start(self, first_kind: str):
        self.kind = first_kind
        q = self._pick()
        self.msg = await self.inter.response.send_message(embed=self._embed(q), view=self)

    async def _next(self, interaction: discord.Interaction, kind: Optional[str] = None):
        if kind:
            self.kind = kind
        q = self._pick()
        await interaction.response.defer()
        if self.msg:
            await self.msg.edit(view=None)
        self.msg = await interaction.followup.send(embed=self._embed(q), view=self)

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.success)
    async def btn_truth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._next(interaction, "truth")

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.danger)
    async def btn_dare(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._next(interaction, "dare")

    @discord.ui.button(label="Random", style=discord.ButtonStyle.primary)
    async def btn_random(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._next(interaction, random.choice(["truth", "dare"]))

@tree.command(name="truth", description="Get a random truth ☺️")
async def truth_cmd(inter: discord.Interaction):
    v = TruthOrDareView(inter)
    await v.start("truth")

@tree.command(name="dare", description="Get a random dare 😈")
async def dare_cmd(inter: discord.Interaction):
    v = TruthOrDareView(inter)
    await v.start("dare")


# ============================================================
# ====================  TRIVIA – KAHOOT  =====================
# ========== Timer, everyone answers, speed-based points =====
# ============================================================

OTDB_BASE = "https://opentdb.com"
OTDB_AMOUNT_MAX = 50

async def otdb_get_token(session: aiohttp.ClientSession) -> Optional[str]:
    try:
        async with session.get(f"{OTDB_BASE}/api_token.php?command=request") as r:
            data = await r.json()
            if data.get("response_code") == 0:
                return data.get("token")
    except Exception:
        return None
    return None

async def otdb_reset_token(session: aiohttp.ClientSession, token: str) -> bool:
    try:
        async with session.get(f"{OTDB_BASE}/api_token.php?command=reset&token={token}") as r:
            data = await r.json()
            return data.get("response_code") == 0
    except Exception:
        return False

def _b64decode(s: str) -> str:
    try:
        return base64.b64decode(s).decode("utf-8")
    except Exception:
        return s

async def otdb_fetch(session: aiohttp.ClientSession, amount: int, token: Optional[str]) -> Tuple[List[Dict], Optional[int]]:
    """
    Returns (questions, response_code_if_any_error)
    Questions as list of dicts:
      {"question": str, "choices": [4], "answer": int}
    """
    amount = max(1, min(OTDB_AMOUNT_MAX, int(amount)))
    url = f"{OTDB_BASE}/api.php?amount={amount}&type=multiple&encode=base64"
    if token:
        url += f"&token={token}"
    try:
        async with session.get(url) as r:
            data = await r.json()
    except Exception:
        return [], 2

    rc = data.get("response_code", 2)
    if rc != 0:
        return [], rc

    out = []
    for item in data.get("results", []):
        q = _b64decode(item.get("question", ""))
        correct = _b64decode(item.get("correct_answer", ""))
        incorrect = [_b64decode(s) for s in item.get("incorrect_answers", [])]
        if len(incorrect) != 3:
            # ensure we only take 4-choice questions
            continue
        choices = incorrect + [correct]
        random.shuffle(choices)
        ans_idx = choices.index(correct)
        out.append({"question": q, "choices": choices, "answer": ans_idx})
    return out, 0

def trivia_q_embed_kahoot(qobj: Dict, qnum: int, total: int, seconds: int, scores: Dict[int,int]) -> discord.Embed:
    e = discord.Embed(
        title=f"Trivia – Q{qnum}/{total} · {seconds}s",
        description=qobj["question"],
        color=discord.Color.gold()
    )
    labels = ["A", "B", "C", "D"]
    for idx, ch in enumerate(qobj["choices"]):
        e.add_field(name=f"{labels[idx]}", value=ch, inline=False)
    if scores:
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:5]
        board = "\n".join([f"<@{uid}> — **{pts}**" for uid, pts in top]) or "—"
        e.add_field(name="Top Scores", value=board, inline=False)
    e.set_footer(text="Pick fast! More time left = more points (correct only).")
    return e

def trivia_result_embed_kahoot(qobj: Dict, qnum: int, total: int,
                               counts: List[int], correct_idx: int,
                               scores: Dict[int,int],
                               winners: List[int]) -> discord.Embed:
    total_answers = sum(counts) or 1
    labels = ["A","B","C","D"]
    bars = []
    for i, cnt in enumerate(counts):
        pct = int(round(100 * cnt / total_answers))
        check = " ✅" if i == correct_idx else ""
        bars.append(f"**{labels[i]}** – {pct}% ({cnt}){check}")
    desc = qobj["question"] + "\n\n" + "\n".join(bars)

    e = discord.Embed(
        title=f"Trivia – Reveal Q{qnum}/{total}",
        description=desc,
        color=discord.Color.green()
    )
    if winners:
        e.add_field(name="Fastest correct", value=", ".join([f"<@{uid}>" for uid in winners[:5]]), inline=False)
    if scores:
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:10]
        e.add_field(
            name="Scoreboard",
            value="\n".join([f"<@{uid}> — **{pts}**" for uid, pts in top]) or "—",
            inline=False
        )
    return e

class TriviaKahootView(discord.ui.View):
    def __init__(self, inter: discord.Interaction, total_q: int, seconds: int):
        super().__init__(timeout=1200.0)
        self.inter = inter
        self.total_target = max(1, min(50, total_q))
        self.seconds = max(5, min(60, seconds))
        self.round_size = self.total_target
        self.current_index = 0
        self.qobj: Optional[Dict] = None
        self.msg: Optional[discord.Message] = None

        # session state
        self.scores: Dict[int,int] = {}                 # user_id -> points
        self.participants: Set[int] = set()             # anyone who clicked
        self.end_votes: Set[int] = set()                # votes to end
        self.answers: Dict[int, Tuple[int, float]] = {} # user_id -> (choice_idx, t_answer)
        self.started_at: float = 0.0                    # unix time per round
        self.timer_task: Optional[asyncio.Task] = None

        # OpenTDB
        self.token: Optional[str] = None
        self.bank: List[Dict] = []

    # ---------- buttons ----------
    @discord.ui.button(label="A", style=discord.ButtonStyle.primary, row=0)
    async def a_btn(self, i: discord.Interaction, b: discord.ui.Button): await self._choose(i, 0)
    @discord.ui.button(label="B", style=discord.ButtonStyle.primary, row=0)
    async def b_btn(self, i: discord.Interaction, b: discord.ui.Button): await self._choose(i, 1)
    @discord.ui.button(label="C", style=discord.ButtonStyle.primary, row=1)
    async def c_btn(self, i: discord.Interaction, b: discord.ui.Button): await self._choose(i, 2)
    @discord.ui.button(label="D", style=discord.ButtonStyle.primary, row=1)
    async def d_btn(self, i: discord.Interaction, b: discord.ui.Button): await self._choose(i, 3)

    @discord.ui.button(label="End (vote)", style=discord.ButtonStyle.danger, row=2)
    async def end_vote(self, i: discord.Interaction, b: discord.ui.Button):
        uid = i.user.id
        self.participants.add(uid)
        if uid in self.end_votes:
            await i.response.send_message("You already voted to end.", ephemeral=True)
            return
        self.end_votes.add(uid)
        threshold = max(1, math.ceil(len(self.participants) / 2))
        if len(self.end_votes) >= threshold:
            await i.response.defer()
            await self._finish("Ended early by majority vote.")
        else:
            remain = threshold - len(self.end_votes)
            await i.response.send_message(f"End vote registered. **{remain}** more needed.", ephemeral=True)

    @discord.ui.button(label="Continue (+batch)", style=discord.ButtonStyle.success, row=2, disabled=True)
    async def continue_btn(self, i: discord.Interaction, b: discord.ui.Button):
        self.continue_btn.disabled = True  # type: ignore
        self.total_target += self.round_size
        self.end_votes.clear()
        await i.response.send_message(f"Continuing! New total: **{self.total_target}**", ephemeral=True)
        await self._next_question(i)

    # ---------- lifecycle ----------
    async def start(self):
        await self.inter.response.send_message(embed=make_embed("Trivia", "Fetching questions…"), ephemeral=False)
        self.msg = await self.inter.original_response()

        async with aiohttp.ClientSession() as session:
            self.token = await otdb_get_token(session)
            self.bank, rc = await otdb_fetch(session, self.total_target, self.token)
            if rc == 4 and self.token:
                # token exhausted, reset once
                await otdb_reset_token(session, self.token)
                self.bank, rc = await otdb_fetch(session, self.total_target, self.token)

        if not self.bank:
            # fallback to local file if available
            if TRIVIA_FALLBACK:
                self.bank = random.sample(TRIVIA_FALLBACK, min(len(TRIVIA_FALLBACK), self.total_target))
            else:
                await self.msg.edit(embed=make_embed("Trivia", "Couldn't fetch questions and no local fallback."), view=None)
                self.stop()
                return

        await self._next_question(self.inter)

    def _current(self) -> Dict:
        # safe pick with wrap
        return self.bank[(self.current_index - 1) % len(self.bank)]

    async def _next_question(self, interaction: discord.Interaction):
        if self.current_index >= self.total_target:
            # set complete
            self.continue_btn.disabled = False  # type: ignore
            done_embed = discord.Embed(
                title="Trivia – Set complete!",
                description="Click **Continue (+batch)** to add more questions or **End (vote)**.",
                color=discord.Color.blurple()
            )
            if self.scores:
                top = sorted(self.scores.items(), key=lambda kv: kv[1], reverse=True)
                board = "\n".join([f"<@{uid}> — **{pts}**" for uid, pts in top]) or "—"
                done_embed.add_field(name="Scores so far", value=board, inline=False)

            if interaction.response.is_done():
                await interaction.followup.send(embed=done_embed, view=self)
            else:
                await interaction.response.edit_message(embed=done_embed, view=self)
            return

        # prepare round
        self.current_index += 1
        self.qobj = self.bank[(self.current_index - 1) % len(self.bank)]
        self.answers.clear()
        self.started_at = time.perf_counter()
        self.end_votes.clear()

        # enable buttons & disable Continue during question
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label in ("A","B","C","D"):
                child.disabled = False
        self.continue_btn.disabled = True  # type: ignore

        emb = trivia_q_embed_kahoot(self.qobj, self.current_index, self.total_target, self.seconds, self.scores)
        if interaction.response.is_done():
            if self.msg:
                await self.msg.edit(embed=emb, view=self)
            else:
                self.msg = await interaction.followup.send(embed=emb, view=self)
        else:
            if self.msg:
                await interaction.response.edit_message(embed=emb, view=self)
            else:
                await interaction.response.send_message(embed=emb, view=self)

        # start/replace timer
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        self.timer_task = asyncio.create_task(self._round_timer())

    async def _choose(self, i: discord.Interaction, choice_idx: int):
        if not self.qobj:
            await i.response.send_message("No question active.", ephemeral=True)
            return
        uid = i.user.id
        self.participants.add(uid)
        if uid in self.answers:
            await i.response.send_message("You've already answered this question.", ephemeral=True)
            return
        t = time.perf_counter()
        self.answers[uid] = (choice_idx, t)
        await i.response.send_message(f"Answer received: **{['A','B','C','D'][choice_idx]}**", ephemeral=True)

    async def _round_timer(self):
        await asyncio.sleep(self.seconds)
        await self._reveal_and_score()

        # small pause then next
        await asyncio.sleep(2.0)
        # use followup edit
        await self._next_question(self.inter)

    async def _reveal_and_score(self):
        if not self.qobj or not self.msg:
            return
        # lock buttons
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label in ("A","B","C","D"):
                child.disabled = True

        # scoring
        correct = self.qobj["answer"]
        counts = [0,0,0,0]
        winners: List[int] = []

        for uid, (choice, t_ans) in self.answers.items():
            counts[choice] += 1
            if choice == correct:
                time_taken = max(0.0, t_ans - self.started_at)
                remaining = max(0.0, self.seconds - time_taken)
                # speed scoring: up to 1000pts; linear on time remaining
                pts = int(500 + 500 * (remaining / self.seconds))
                self.scores[uid] = self.scores.get(uid, 0) + pts
                winners.append(uid)

        # build reveal embed
        emb = trivia_result_embed_kahoot(
            self.qobj, self.current_index, self.total_target,
            counts, correct, self.scores, winners
        )
        await self.msg.edit(embed=emb, view=self)

    async def _finish(self, reason: str):
        # stop timer
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()

        # disable all buttons
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

        # final scoreboard
        emb = discord.Embed(title="Trivia – Finished", description=reason, color=discord.Color.dark_gold())
        if self.scores:
            top = sorted(self.scores.items(), key=lambda kv: kv[1], reverse=True)
            lines = []
            medal = ["🥇","🥈","🥉"]
            for idx, (uid, pts) in enumerate(top, start=1):
                prefix = medal[idx-1] if idx <= 3 else f"{idx}."
                lines.append(f"{prefix} <@{uid}> — **{pts}**")
            emb.add_field(name="Final Scores", value="\n".join(lines), inline=False)
            winner_ids = [uid for uid, pts in top if pts == top[0][1]]
            if len(winner_ids) == 1:
                emb.add_field(name="Winner", value=f"<@{winner_ids[0]}>", inline=False)
            else:
                winners = ", ".join([f"<@{uid}>" for uid in winner_ids])
                emb.add_field(name="Winners (tie)", value=winners, inline=False)
        else:
            emb.add_field(name="Final Scores", value="No points awarded.", inline=False)

        if self.msg:
            await self.msg.edit(embed=emb, view=self)
        self.stop()

@tree.command(name="trivia", description="Play Kahoot-style trivia (timer, speed points, API-backed).")
@app_commands.describe(
    questions="How many questions in this set (1-50)",
    timer="Seconds per question (5-60)"
)
async def trivia_cmd(
    inter: discord.Interaction,
    questions: Optional[app_commands.Range[int,1,50]] = 10,
    timer: Optional[app_commands.Range[int,5,60]] = 15
):
    v = TriviaKahootView(inter, total_q=questions or 10, seconds=timer or 15)
    await v.start()


# ============================================================
# =======================  MINI-GAMES  =======================
# ============================================================

# ---- Coinflip ----
@tree.command(name="coinflip", description="Flip a coin.")
async def coinflip(inter: discord.Interaction):
    await inter.response.send_message(f"🪙 {random.choice(['Heads', 'Tails'])}")

# ---- Dice roll (NdM+K) ----
DICE_RE = re.compile(r"^\s*(\d+)[dD](\d+)([+-]\d+)?\s*$")

@tree.command(name="roll", description="Roll dice (e.g., 2d6+1).")
async def roll(inter: discord.Interaction, dice: str):
    m = DICE_RE.match(dice)
    if not m:
        await inter.response.send_message("Format: `NdM(+/-K)` e.g. `2d6+1`", ephemeral=True)
        return
    n, sides, mod = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    if n <= 0 or sides <= 1 or n > 100:
        await inter.response.send_message("Invalid dice.", ephemeral=True)
        return
    rolls = [random.randint(1, sides) for _ in range(n)]
    total = sum(rolls) + mod
    await inter.response.send_message(f"🎲 Rolls: {rolls} {'+' if mod>=0 else ''}{mod}\n**Total:** {total}")

# ---- Rock–Paper–Scissors: lobby + match with rematch & score (victory embed) ----

RPS_CHOICES = ("rock", "paper", "scissors")
RPS_BEATS = {("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")}

def rps_result(a: str, b: str) -> int:
    if a == b: return 0
    return 1 if (a, b) in RPS_BEATS else -1

def rps_vs_line(p1: discord.Member, c1: Optional[str], p2: discord.Member, c2: Optional[str], reveal: bool) -> str:
    left  = c1 if (reveal and c1) else ("…" if c1 else "—")
    right = c2 if (reveal and c2) else ("…" if c2 else "—")
    return f"**{p1.display_name}** ({left})  vs  **{p2.display_name}** ({right})"

def rps_score_line(scores: Dict[int, int], p1: discord.Member, p2: discord.Member) -> str:
    s1 = scores.get(p1.id, 0)
    s2 = scores.get(p2.id, 0)
    return f"**Score:** {p1.display_name} {s1} — {s2} {p2.display_name}"

def rps_embed(title: str, desc: str, p1: discord.Member, p2: discord.Member, scores: Dict[int, int]) -> discord.Embed:
    e = make_embed(title, desc, discord.Color.blurple())
    e.add_field(name="Players", value=f"{p1.mention} vs {p2.mention}", inline=False)
    e.add_field(name="Score", value=rps_score_line(scores, p1, p2), inline=False)
    return e

def rps_victory_embed(p1: discord.Member, p2: discord.Member, scores: Dict[int,int]) -> discord.Embed:
    s1, s2 = scores.get(p1.id,0), scores.get(p2.id,0)
    if s1 == s2:
        title = "RPS – Match Over (Tie)"
        desc = f"Tied at **{s1}**–**{s2}**!"
    elif s1 > s2:
        title = "RPS – Victory!"
        desc = f"**{p1.display_name}** wins **{s1}**–**{s2}** over **{p2.display_name}**"
    else:
        title = "RPS – Victory!"
        desc = f"**{p2.display_name}** wins **{s2}**–**{s1}** over **{p1.display_name}**"
    return make_embed(title, desc, discord.Color.green())

class RPSMatchView(discord.ui.View):
    def __init__(self, p1: discord.Member, p2: discord.Member):
        super().__init__(timeout=600.0)
        self.p1 = p1
        self.p2 = p2
        self.choices: Dict[int, Optional[str]] = {p1.id: None, p2.id: None}
        self.scores: Dict[int, int] = {p1.id: 0, p2.id: 0}
        self.round_no = 1
        self.msg: Optional[discord.Message] = None

    async def start(self, interaction: discord.Interaction):
        txt = "Click a button below to choose. Your pick is private until both have chosen."
        emb = rps_embed(f"RPS – Round {self.round_no}", txt, self.p1, self.p2, self.scores)
        self.msg = await interaction.followup.send(embed=emb, view=self)

    def _guard_player(self, u: discord.abc.User) -> bool:
        return u.id in self.choices

    async def _handle_pick(self, interaction: discord.Interaction, pick: str):
        if not self._guard_player(interaction.user):
            await interaction.response.send_message("You're not in this match.", ephemeral=True)
            return
        if self.choices[interaction.user.id] is not None:
            await interaction.response.send_message("You already picked this round.", ephemeral=True)
            return
        self.choices[interaction.user.id] = pick
        await interaction.response.send_message(f"You picked **{pick}**.", ephemeral=True)

        if all(self.choices.values()):
            c1 = self.choices[self.p1.id]
            c2 = self.choices[self.p2.id]
            res = rps_result(c1, c2)  # type: ignore

            if res == 1:
                self.scores[self.p1.id] += 1
                verdict = f"**{self.p1.display_name}** wins this round!"
            elif res == -1:
                self.scores[self.p2.id] += 1
                verdict = f"**{self.p2.display_name}** wins this round!"
            else:
                verdict = "**Tie!**"

            desc = rps_vs_line(self.p1, c1, self.p2, c2, reveal=True) + f"\n{verdict}"
            emb = rps_embed(f"RPS – Round {self.round_no} result", desc, self.p1, self.p2, self.scores)

            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id in ("rps_rematch", "rps_end"):
                    child.disabled = False

            await self.msg.edit(embed=emb, view=self)

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary, row=0, custom_id="rps_rock")
    async def btn_rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_pick(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.secondary, row=0, custom_id="rps_paper")
    async def btn_paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_pick(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.secondary, row=0, custom_id="rps_scissors")
    async def btn_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_pick(interaction, "scissors")

    @discord.ui.button(label="Rematch", style=discord.ButtonStyle.success, row=1, disabled=True, custom_id="rps_rematch")
    async def btn_rematch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._guard_player(interaction.user):
            await interaction.response.send_message("Only the current players can request a rematch.", ephemeral=True)
            return
        self.round_no += 1
        self.choices[self.p1.id] = None
        self.choices[self.p2.id] = None

        self.btn_rematch.disabled = True  # type: ignore
        desc = rps_vs_line(self.p1, None, self.p2, None, reveal=False) + "\nNew round! Pick again."
        emb = rps_embed(f"RPS – Round {self.round_no}", desc, self.p1, self.p2, self.scores)
        await interaction.response.edit_message(embed=emb, view=self)

    @discord.ui.button(label="End", style=discord.ButtonStyle.danger, row=1, disabled=True, custom_id="rps_end")
    async def btn_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._guard_player(interaction.user):
            await interaction.response.send_message("Only the current players can end the match.", ephemeral=True)
            return
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        emb = rps_embed("RPS – Match finished",
                        f"Final: {rps_score_line(self.scores, self.p1, self.p2)}",
                        self.p1, self.p2, self.scores)
        await interaction.response.edit_message(embed=emb, view=self)
        await interaction.followup.send(embed=rps_victory_embed(self.p1, self.p2, self.scores))
        self.stop()


class RPSLobbyView(discord.ui.View):
    def __init__(self, starter: discord.Member, opponent: Optional[discord.Member] = None):
        super().__init__(timeout=180.0)
        self.starter = starter
        self.opponent = opponent
        self.joined: List[discord.Member] = [starter] if opponent is None else []
        self.msg: Optional[discord.Message] = None

        if opponent is None:
            self.add_item(self.JoinBtn(self))
        else:
            self.add_item(self.AcceptBtn(self))
            self.add_item(self.DeclineBtn(self))

    class JoinBtn(discord.ui.Button):
        def __init__(self, lobby: 'RPSLobbyView'):
            super().__init__(label="Join", style=discord.ButtonStyle.primary)
            self.lobby = lobby

        async def callback(self, interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Only guild members can join.", ephemeral=True)
                return
            if interaction.user in self.lobby.joined:
                await interaction.response.send_message("You're already in!", ephemeral=True)
                return
            if len(self.lobby.joined) >= 2:
                await interaction.response.send_message("Two players already joined.", ephemeral=True)
                return

            self.lobby.joined.append(interaction.user)
            await interaction.response.send_message(f"You joined! ({len(self.lobby.joined)}/2)", ephemeral=True)

            if len(self.lobby.joined) == 2:
                p1, p2 = self.lobby.joined
                match = RPSMatchView(p1, p2)
                if self.lobby.msg:
                    try:
                        await self.lobby.msg.edit(content=f"**RPS Match:** {p1.mention} vs {p2.mention}", view=None)
                    except Exception:
                        pass
                await match.start(interaction)

    class AcceptBtn(discord.ui.Button):
        def __init__(self, lobby: 'RPSLobbyView'):
            super().__init__(label="Accept Challenge", style=discord.ButtonStyle.success)
            self.lobby = lobby

        async def callback(self, interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Only guild members can accept.", ephemeral=True)
                return
            if interaction.user.id != self.lobby.opponent.id:
                await interaction.response.send_message("This challenge isn't for you.", ephemeral=True)
                return

            p1 = self.lobby.starter
            p2 = self.lobby.opponent
            match = RPSMatchView(p1, p2)

            await interaction.response.edit_message(content=f"**RPS Match:** {p1.mention} vs {p2.mention}", view=None)
            await match.start(interaction)

    class DeclineBtn(discord.ui.Button):
        def __init__(self, lobby: 'RPSLobbyView'):
            super().__init__(label="Decline", style=discord.ButtonStyle.danger)
            self.lobby = lobby

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.lobby.opponent.id:
                await interaction.response.send_message("Only the challenged user can decline.", ephemeral=True)
                return
            await interaction.response.edit_message(content="Challenge declined.", view=None)
            self.lobby.stop()

    async def send(self, interaction: discord.Interaction):
        if self.opponent is None:
            text = f"**RPS Free-for-all!** First two people to press **Join** will play."
        else:
            text = (
                f"**RPS Challenge:** {self.starter.mention} vs {self.opponent.mention}\n"
                f"{self.opponent.mention}, press **Accept** to start."
            )
        await interaction.response.send_message(text, view=self)
        self.msg = await interaction.original_response()

@tree.command(name="rps", description="Rock–Paper–Scissors: free-for-all or challenge a user.")
@app_commands.describe(opponent="Optionally challenge a specific user")
async def rps(inter: discord.Interaction, opponent: Optional[discord.Member] = None):
    lobby = RPSLobbyView(inter.user, opponent=opponent)
    await lobby.send(inter)


# ---- Tic-Tac-Toe (victory embed) ----
T3_WIN = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

class TTT(discord.ui.View):
    def __init__(self, inter: discord.Interaction, p2: discord.Member):
        super().__init__(timeout=300.0)
        self.inter = inter
        self.p1 = inter.user
        self.p2 = p2
        self.turn = self.p1
        self.board = [' '] * 9
        self.msg: Optional[discord.Message] = None

        for i in range(9):
            self.add_item(self.Cell(i, self))

    class Cell(discord.ui.Button):
        def __init__(self, idx: int, game: 'TTT'):
            super().__init__(label="⬜", style=discord.ButtonStyle.secondary, row=idx//3)
            self.idx = idx
            self.game = game
        async def callback(self, interaction: discord.Interaction):
            g = self.game
            if interaction.user.id != g.turn.id:
                await interaction.response.send_message("Not your turn.", ephemeral=True)
                return
            if g.board[self.idx] != ' ':
                await interaction.response.send_message("Cell already taken.", ephemeral=True)
                return
            mark = 'X' if g.turn.id == g.p1.id else 'O'
            g.board[self.idx] = mark
            self.label = mark
            self.style = discord.ButtonStyle.success if mark == 'X' else discord.ButtonStyle.danger
            self.disabled = True
            g.turn = g.p2 if g.turn.id == g.p1.id else g.p1

            state = g._state_text()
            win = g._winner()
            if win:
                for item in g.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                await interaction.response.edit_message(content=state + f"\n**Winner:** {win.mention}", view=g)
                v = make_embed("Tic-Tac-Toe – Victory!", f"Winner: {win.mention}", discord.Color.green())
                await interaction.followup.send(embed=v)
                g.stop()
            elif ' ' not in g.board:
                for item in g.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                await interaction.response.edit_message(content=state + "\n**Draw!**", view=g)
                v = make_embed("Tic-Tac-Toe – Draw", "No more moves left.", discord.Color.orange())
                await interaction.followup.send(embed=v)
                g.stop()
            else:
                await interaction.response.edit_message(content=state + f"\nTurn: {g.turn.mention}", view=g)

    def _winner(self) -> Optional[discord.Member]:
        for a,b,c in T3_WIN:
            if self.board[a] != ' ' and self.board[a] == self.board[b] == self.board[c]:
                return self.p1 if self.board[a] == 'X' else self.p2
        return None

    def _state_text(self) -> str:
        rows = [' | '.join(self.board[r*3:(r+1)*3]) for r in range(3)]
        return "```\n" + "\n---------\n".join(rows) + "\n```"

    async def start(self):
        e = make_embed("Tic-Tac-Toe", f"{self.p1.mention} (X) vs {self.p2.mention} (O)")
        self.msg = await self.inter.response.send_message(
            content=self._state_text() + f"\nTurn: {self.turn.mention}",
            embed=e,
            view=self
        )

@tree.command(name="tictactoe", description="Challenge someone to Tic-Tac-Toe.")
async def tictactoe_cmd(inter: discord.Interaction, opponent: discord.Member):
    if opponent.bot:
        await inter.response.send_message("Pick a human opponent :)", ephemeral=True)
        return
    game = TTT(inter, opponent)
    await game.start()


# ============================================================
# =====================  BOOT & PRESENCE  ====================
# ============================================================

@client.event
async def on_ready():
    try:
        await tree.sync()
    except Exception:
        pass
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    await client.change_presence(activity=discord.Game(name="/help"))

if __name__ == "__main__":
    os.makedirs(os.path.dirname(TRIVIA_PATH), exist_ok=True)
    client.run(TOKEN)

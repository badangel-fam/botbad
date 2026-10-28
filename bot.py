import os
import asyncio
import discord
from discord.ext import commands
from gtts import gTTS

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

BOT_TOKEN = os.getenv("BOT_TOKEN")
raw_channel_id = os.getenv("VOICE_CHANNEL_ID")

print(f"DEBUG_START: Raw VOICE_CHANNEL_ID = [{raw_channel_id}]")

try:
    TARGET_VOICE_CHANNEL_ID = int(raw_channel_id.strip()) if raw_channel_id else None
except Exception as e:
    print(f"DEBUG_ERROR: Failed to parse channel ID: {e}")
    TARGET_VOICE_CHANNEL_ID = None

print(f"DEBUG_START: Converted TARGET_VOICE_CHANNEL_ID = [{TARGET_VOICE_CHANNEL_ID}]")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    bot.loop.create_task(maintain_voice_connection())

async def maintain_voice_connection():
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    
    print(f"VA: Starting voice connection loop with ID: {TARGET_VOICE_CHANNEL_ID}")
    
    while not bot.is_closed():
        try:
            if not TARGET_VOICE_CHANNEL_ID:
                print("VA_ERROR: TARGET_VOICE_CHANNEL_ID is None or invalid!")
                await asyncio.sleep(10)
                continue

            channel = bot.get_channel(TARGET_VOICE_CHANNEL_ID)
            print(f"VA: Fetched channel object -> {channel}")
            
            if channel and isinstance(channel, discord.VoiceChannel):
                voice_client = channel.guild.voice_client
                
                if not voice_client or not voice_client.is_connected() or voice_client.channel != channel:
                    if voice_client:
                        try:
                            await voice_client.disconnect(force=True)
                        except:
                            pass
                    
                    await channel.connect(self_deaf=True)
                    print(f"VA: Successfully connected to voice channel: {channel.name}")
            else:
                print(f"VA_WARNING: Channel not found! Check if bot is in the server and ID is correct.")
        except Exception as e:
            print(f"VA_EXCEPTION: {e}")
        
        await asyncio.sleep(5)

@bot.tree.command(name="say", description="พิมพ์ข้อความเพื่อให้บอทพูด")
async def say(interaction: discord.Interaction, text: str):
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียง!", ephemeral=True)
        return
    await interaction.response.send_message(f"พูดว่า: `{text}`", ephemeral=True)
    try:
        tts = gTTS(text=text, lang='th')
        path = "say.mp3"
        tts.save(path)
        while voice_client.is_playing():
            await asyncio.sleep(1)
        voice_client.play(discord.FFmpegPCMAudio(path))
    except Exception as e:
        print(f"TTS Error: {e}")

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return
    voice_client = member.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return
    
    current_bot_channel = voice_client.channel
    msg = None
    if after.channel == current_bot_channel and before.channel != current_bot_channel:
        msg = f"อี {member.display_name} เสร่อเข้ามาแล้ว"
    elif before.channel == current_bot_channel and after.channel != current_bot_channel:
        msg = f"อี {member.display_name} อีช้างลากเย็ดไปไหนละอีควย"

    if msg:
        try:
            tts = gTTS(text=msg, lang='th')
            path = "notify.mp3"
            tts.save(path)
            while voice_client.is_playing():
                await asyncio.sleep(1)
            voice_client.play(discord.FFmpegPCMAudio(path))
        except Exception as e:
            print(f"Notify Error: {e}")

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Error: BOT_TOKEN missing!")

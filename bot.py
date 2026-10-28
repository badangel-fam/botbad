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

# ดึงค่า Token และ Channel ID จาก Environment/Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
raw_channel_id = os.getenv("VOICE_CHANNEL_ID")

print(f"DEBUG: Raw VOICE_CHANNEL_ID from env -> '{raw_channel_id}'")

try:
    TARGET_VOICE_CHANNEL_ID = int(raw_channel_id) if raw_channel_id else None
except ValueError:
    TARGET_VOICE_CHANNEL_ID = None

print(f"DEBUG: Converted TARGET_VOICE_CHANNEL_ID -> {TARGET_VOICE_CHANNEL_ID}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await asyncio.sleep(5)
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Sync error: {e}")

    bot.loop.create_task(maintain_voice_connection())

async def maintain_voice_connection():
    await bot.wait_until_ready()
    await asyncio.sleep(10)
    
    print(f"Target Voice Channel ID to search: {TARGET_VOICE_CHANNEL_ID}")
    
    while not bot.is_closed():
        try:
            if not TARGET_VOICE_CHANNEL_ID:
                print("ERROR: TARGET_VOICE_CHANNEL_ID is missing or invalid!")
                await asyncio.sleep(10)
                continue

            channel = bot.get_channel(TARGET_VOICE_CHANNEL_ID)
            print(f"Fetched channel object: {channel}")
            
            if channel and isinstance(channel, discord.VoiceChannel):
                voice_client = channel.guild.voice_client
                
                if not voice_client or not voice_client.is_connected() or voice_client.channel != channel:
                    if voice_client:
                        try:
                            await voice_client.disconnect(force=True)
                        except:
                            pass
                    
                    await channel.connect(self_deaf=True)
                    print(f"Successfully connected to voice channel: {channel.name}")
            else:
                print(f"WARNING: Could not find voice channel with ID {TARGET_VOICE_CHANNEL_ID}. Make sure the bot is in the server and the ID is correct.")
        except Exception as e:
            print(f"Voice connection error: {e}")
        
        await asyncio.sleep(5)

@bot.tree.command(name="say", description="พิมพ์ข้อความเพื่อให้บอทพูดออกมาเป็นเสียง")
async def say(interaction: discord.Interaction, text: str):
    voice_client = interaction.guild.voice_client

    if not voice_client or not voice_client.is_connected():
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียงตอนนี้!", ephemeral=True)
        return

    await interaction.response.send_message(f"กำลังพูดว่า: `{text}`", ephemeral=True)

    try:
        tts = gTTS(text=text, lang='th')
        audio_file = "tts_output.mp3"
        tts.save(audio_file)

        while voice_client.is_playing():
            await asyncio.sleep(1)

        voice_client.play(discord.FFmpegPCMAudio(audio_file))

        while voice_client.is_playing():
            await asyncio.sleep(1)
        
        if os.path.exists(audio_file):
            os.remove(audio_file)
    except Exception as e:
        print(f"Error generating/playing TTS: {e}")

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return

    voice_client = member.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return

    current_bot_channel = voice_client.channel
    announcement_text = None

    if after.channel == current_bot_channel and before.channel != current_bot_channel:
        announcement_text = f"อี {member.display_name} เสร่อเข้ามาแล้ว"
    elif before.channel == current_bot_channel and after.channel != current_bot_channel:
        announcement_text = f"อี {member.display_name} อีช้างลากเย็ดไปไหนละอีควย"

    if announcement_text:
        try:
            tts = gTTS(text=announcement_text, lang='th')
            audio_file = "notify_output.mp3"
            tts.save(audio_file)

            while voice_client.is_playing():
                await asyncio.sleep(1)

            voice_client.play(discord.FFmpegPCMAudio(audio_file))

            while voice_client.is_playing():
                await asyncio.sleep(1)

            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as e:
            print(f"Error in voice notification: {e}")

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Error: BOT_TOKEN is missing!")

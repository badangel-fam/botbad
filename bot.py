import os
import asyncio
import discord
from discord.ext import commands
from gtts import gTTS

# ตั้งค่า Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ดึงค่าจากระบบ Environment Variables ของเว็บโฮสต์ (ปลอดภัย ไม่ต้องใส่ Token ตรงๆ ในโค้ด)
TARGET_VOICE_CHANNEL_ID = int(os.environ.get("VOICE_CHANNEL_ID", 123456789012345678))
BOT_TOKEN = os.environ.get("BOT_TOKEN")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(e)

    bot.loop.create_task(maintain_voice_connection())

async def maintain_voice_connection():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            channel = bot.get_channel(TARGET_VOICE_CHANNEL_ID)
            if channel and isinstance(channel, discord.VoiceChannel):
                if not channel.guild.voice_client or channel.guild.voice_client.channel != channel:
                    if channel.guild.voice_client:
                        await channel.guild.voice_client.disconnect(force=True)
                    
                    await channel.connect(self_deaf=True)
                    print(f"Connected to voice channel: {channel.name}")
        except Exception as e:
            print(f"Voice connection error: {e}")
        
        await asyncio.sleep(30)


@bot.tree.command(name="say", description="พิมพ์ข้อความเพื่อให้บอทพูดออกมาเป็นเสียงในห้องแชท")
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

        audio_source = discord.FFmpegPCMAudio(audio_file)
        voice_client.play(audio_source)

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

bot.run(BOT_TOKEN)
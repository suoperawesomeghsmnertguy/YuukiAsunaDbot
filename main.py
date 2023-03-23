import os, discord, requests, asyncio, openai
from google.cloud import texttospeech as tts
from discord.ext import commands

openai.api_key = "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"
ai_context = open("context.txt", "r").read()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.ext.commands.Bot(command_prefix="", intents=intents)

def convert_to_audio(prompt) -> bool:
    client = tts.TextToSpeechClient()
    voice_response = client.synthesize_speech(
        input = tts.SynthesisInput(text = prompt),
        voice = tts.VoiceSelectionParams(
            language_code = "en-US", 
            name = "en-US-Wavenet-F",
        ),
        audio_config = tts.AudioConfig(
            volume_gain_db = 0.0,
            speaking_rate = 1.25,
            pitch = 1.0,
            audio_encoding = tts.AudioEncoding.MP3
        )
    )
    with open("output.mp3", "wb") as out:
        out.write(voice_response.audio_content)
    return True

def get_response(input) -> str:
    input = input.encode(encoding="ASCII", errors="ignore").decode()
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        presence_penalty = 2.0,
        frequency_penalty = 2.0,
        max_tokens = 800,
        messages = [
            { "role": "system", "content": ai_context },
            { "role": "user",   "content": input }
        ]
    )
    return response['choices'][0]['message']['content'].strip()

async def analyze_voice_data(sink, ctx):
    for audio in sink.audio_data.values():
        await ctx.bot.change_presence(activity = discord.Activity(type=discord.ActivityType.listening, name="Analyzing Audio. . ."))
        file = open(audio.file, "rb")
        transcript = openai.Audio.transcribe("whisper-1", file)
        text = transcript["text"]
        await ctx.send(f"transcribed as: '" + text + "'")
        await do_ai_stuff(text, ctx)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    

@bot.command()
async def join(ctx):
    await ctx.author.voice.channel.connect()


@bot.command(name="1")
async def begin(ctx):
    if ctx.voice_client == None:
        await ctx.author.voice.channel.connect()
    if ctx.voice_client != None:
        await ctx.send("started recording for id: " + str(ctx.author.id))
        try:
            ctx.voice_client.start_recording(discord.Sink(encoding="mp3",filters={"users": [ctx.author.id]}), lambda sink, ctx=ctx: analyze_voice_data(sink, ctx))
            await ctx.bot.change_presence(activity = discord.Activity(type=discord.ActivityType.listening, name="Recording. . ."))
        except:
            ctx.send("i'm already recording nigga...")


@bot.command(name="2")
async def end(ctx):
    if ctx.voice_client == None:
        await ctx.author.voice.channel.connect()
    if ctx.voice_client != None:
        await ctx.send("stopped recording.")
        ctx.voice_client.stop_recording()

@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()

@bot.command()
async def Yuuki(ctx, *, prompt):
    if ctx.voice_client == None:
        await ctx.author.voice.channel.connect()
    if prompt == "": return
    await do_ai_stuff(prompt, ctx)

async def do_ai_stuff(prompt, ctx):
    if prompt == "": return
    response = get_response(prompt)
    await ctx.send(response)
    if ctx.voice_client != None:
        if convert_to_audio(response):
            await ctx.bot.change_presence(activity = discord.Streaming(name="Audio", url="https://www.youtube.com/watch?v=mRKCgX1WGTA"))
            ctx.voice_client.play(discord.FFmpegPCMAudio("output.mp3"))
            

@bot.command(name='dalle', help='Generates an image using DALL-E 2.0.')
async def generate_image(ctx, *, prompt):
    print("command dalle used")
    prompt_text = ' '.join(prompt)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai.api_key}',
    }
    data = {
        'model': 'image-alpha-001',
        'prompt': prompt_text,
        'num_images': 1,
    }
    response = requests.post('https://api.openai.com/v1/images/generations', headers=headers, json=data)
    if response.status_code == 200:
        json_response = response.json()
        image_url = json_response['data'][0]['url']
        await ctx.send(f'Here is your generated image: {image_url}')
    else:
        await ctx.send(f'An error occurred while generating the image')

bot.run("NjMxNjU4MDA2NTY3NzE0ODI2.GPyCAY.Lx8YAzpQmhr71x0FwuEOoVhXZLNLzOf7e086bY")
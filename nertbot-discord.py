from nertbot import processScreenshot
import discord
from dotenv import load_dotenv
import os
from PIL import Image
import io
import cv2
import numpy as np

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if client.user in message.mentions:
        print("nertbot was mentioned!")
        if message.attachments != []:
            try:
                attachment = message.attachments[0]
                f = io.BytesIO()
                await attachment.save(f)
                print("image downloaded")
                f.seek(0)
                file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                print("parsing image")
                plotBuffer = processScreenshot(image)
                await message.channel.send(file=discord.File(fp=plotBuffer, filename='nertbot-plot.png'))
            except:
                await message.channel.send("Could not parse image, sorry")


client.run(TOKEN)
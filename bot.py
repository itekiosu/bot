import cmyui
import glob
from discord.ext import commands
import discord.utils
import random
import string

db = cmyui.AsyncSQLPool()
await db.connect(glob.config.mysql)
client = commands.Bot(command_prefix=glob.config.prefix)

@client.command()
async def generate(ctx):
    if ctx.channel.id == glob.config.generate_channel:
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{ctx.author}")')
        await ctx.delete()
        return await ctx.author.send(f'Key generated!\n\nKey: `{key}`')

@client.command()
async def accept(ctx):
    mention = ctx.message.mentions
    for user in mention:
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{ctx.author}")')
        await ctx.delete()
        await user.send(f'Key generated!\n\nKey: `{key}`')
        await user.add_roles('Beta Tester')

client.run(glob.config.token)

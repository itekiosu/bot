import cmyui
import glob
from discord.ext import commands
import discord.utils
import discord
import random
import string

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=glob.config.prefix, intents=intents)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=glob.config.member_role)
    await member.add_roles(role)

@bot.command()
async def generate(ctx):
    db = cmyui.AsyncSQLPool()
    await db.connect(glob.config.mysql)
    if ctx.channel.id == glob.config.generate_channel:
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{ctx.author}")')
        await ctx.delete()
        return await ctx.author.send(f'Key generated!\n\nKey: `{key}`')

@bot.command()
async def accept(ctx):
    db = cmyui.AsyncSQLPool()
    await db.connect(glob.config.mysql)
    mention = ctx.message.mentions
    await ctx.message.delete()
    for user in mention:
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{ctx.author}")')
        await user.send(f'Key generated!\n\nKey: `{key}`')
        role = discord.utils.get(user.guild.roles, name=glob.config.beta_role)
        await user.add_roles(role)

bot.run(glob.config.token)
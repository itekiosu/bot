import cmyui
import glob
from discord.ext import commands
import discord.utils
import discord
import random
import string
import aiohttp
import aiofiles

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=glob.config.prefix, intents=intents)
db = cmyui.AsyncSQLPool()

@bot.event
async def on_ready():
    await db.connect(glob.config.mysql)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=glob.config.member_role)
    await member.add_roles(role)

@bot.command()
async def generate(ctx):
    if ctx.channel.id == glob.config.generate_channel:
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{ctx.author}")')
        await ctx.message.delete()
        return await ctx.author.send(f'Key generated!\n\nKey: `{key}`')

@bot.command()
async def accept(ctx):
    mention = ctx.message.mentions
    await ctx.message.delete()
    for user in mention:
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{ctx.author}")')
        await user.send(f'Key generated!\n\nKey: `{key}`')
        role = discord.utils.get(user.guild.roles, name=glob.config.beta_role)
        return await user.add_roles(role)

@bot.command()
async def avatar(ctx, url: str = None):
    if url is None:
        try:
            url = ctx.message.attachments[0].url
        except:
            return await ctx.send('Please ensure you provide either an image by URL or file upload! (Syntax: `!avatar <url if you are not using image upload>`)')
    a = await db.fetch(f'SELECT user FROM discord WHERE tag = "{ctx.author}"')
    if a is not None:
        if a['user'] != 0:
            uid = a['user']
        else:
            return await ctx.send("You haven't finished the linking process! Please check your DMs with @Iteki#5497 and follow the instructions to finish the linking process, then try again.")
    else:
        return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status == 200:
                file = await aiofiles.open(f'/home/iteki/gulag/.data/avatars/{uid}.png', 'wb')
                await file.write(await res.read())
                await file.close()
                e = await db.fetch(f'SELECT name FROM users WHERE id = {uid}')
                uname = e['name']
                return await ctx.send(f'Ok **{uname}**, your avatar has been changed! Please restart your game for it to update.')

@bot.command()
async def link(ctx):
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    e = await db.fetch(f'SELECT 1 FROM discord WHERE tag = "{ctx.author}"')
    await ctx.message.delete()
    if not e:
        await db.execute(f'INSERT INTO discord (tag, user, code) VALUES ("{ctx.author}", 0, "{code}")')
        return await ctx.author.send(f'Linking account initiated!\n\nTo finalise the process, please login ingame and send this command to Ruji:\n`!link {code}`')
    else:
        return await ctx.author.send("Your Discord is already linked to an Iteki account! If you think this is in error, please DM mbruhyo#8551 on Discord.")

bot.run(glob.config.token)
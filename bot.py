import cmyui
import glob
from cmyui.discord import Webhook, Embed
from discord.ext import commands
from PIL import Image
import discord.utils
import discord
import random
import string
import aiohttp
import aiofiles
from resizeimage import resizeimage

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=glob.config.prefix, intents=intents)
db = cmyui.AsyncSQLPool()

async def get_info_id(user):
    e = await db.fetch(f'SELECT name FROM users WHERE id = {user}')
    f = await db.fetch(f'SELECT tag_id FROM discord WHERE id = {user}')
    if f['tag_id'] is not None:
        discord = f['tag_id']
    else:
        discord = None
    return [e['name'], discord]

async def get_info(discord):
    f = await db.fetch(f'SELECT user FROM discord WHERE tag_id = {discord}')
    e = await db.fetch(f'SELECT name FROM users WHERE id = {f["id"]}')
    return [e['name'], f['id']]

async def get_info_name(user):
    e = await db.fetch(f'SELECT id FROM users WHERE safe_name = {user.lower()}')
    f = await db.fetch(f'SELECT tag_id FROM discord WHERE id = {e["id"]}')
    if f['tag_id'] is not None:
        discord = f['tag_id']
    else:
        discord = None
    return [e['id'], discord]

async def check_link(discord):
    e = await db.fetch(f'SELECT user FROM discord WHERE tag_id = {discord}')
    if e is not None:
        if e['user'] != 0:
            return True
        else:
            return False
    else:
        return False

async def check_link_id(user):
    e = await db.fetch(f'SELECT tag FROM discord WHERE id = {user}')
    if e['tag'] is not None:
        return e['tag']
    else:
        return False

@bot.event
async def on_ready():
    await db.connect(glob.config.mysql)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=glob.config.member_role)
    await member.add_roles(role)

@bot.command()
async def generate(ctx):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{ctx.author}")')
        await ctx.message.delete()
        return await ctx.author.send(f'Key generated!\n\nKey: `{key}`')
    else:
        return await ctx.send("You don't have permissions to do that!")

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
    a = await db.fetch(f'SELECT user FROM discord WHERE tag_id = {ctx.author.id}')
    if await check_link(ctx.author):
        uid = a['user']
    else:
        return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status == 200:
                file = await aiofiles.open(f'/home/iteki/gulag/.data/avatars/{uid}.png', 'wb')
                await file.write(await res.read())
                await file.close()
                img = Image.open(f'/home/iteki/gulag/.data/avatars/{uid}.png')
                width, height = img.size
                if width > 256 or height > 256:
                    new = resizeimage.resize_cover(img, [256, 256])
                    new.save(f'/home/iteki/gulag/.data/avatars/{uid}.png', img.format)
                e = await db.fetch(f'SELECT name FROM users WHERE id = {uid}')
                uname = e['name']
                return await ctx.send(f'Ok **{uname}**, your avatar has been changed! Please restart your game for it to update.')
            else:
                return await ctx.send(f'Error getting image! If you provided a URL, please ensure that anyone has the permission to view this image.')

@bot.command()
async def link(ctx):
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    if not await check_link(ctx.author):
        await db.execute(f'INSERT INTO discord (tag, user, code, tag_id) VALUES ("{ctx.author}", 0, "{code}", {ctx.author.id})')
        await ctx.send('Linking initiated! Please check your DMs for further instructions.')
        return await ctx.author.send(f'To finalise the linking process, please login ingame and send this command to Ruji:\n`!link {code}`')
    else:
        return await ctx.author.send("Your Discord is already linked to an Iteki account! If you think this is in error, please DM @mbruhyo#8551 on Discord.")

@bot.command()
async def purge(ctx, amount: int = 0):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        if amount == 0:
            await ctx.message.delete()
            await ctx.channel.purge()
            await ctx.send(f'{ctx.author.mention} purged everything in {ctx.channel.mention}!', delete_after=2)
        else:
            await ctx.message.delete()
            await ctx.channel.purge(limit=amount)
            await ctx.send(f'{ctx.author.mention} purged {amount} messages in {ctx.channel.mention}!', delete_after=2)
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def ban(ctx, reason: str = None):
    user = ctx.message.mentions
    for mention in user:
        await mention.ban(reason=reason)
        return await ctx.send('User has been banned!')

@bot.command()
async def unban(ctx, reason: str = None):
    user = ctx.message.mentions
    for mention in user:
        await mention.unban(reason=reason)
        return await ctx.send('User has been unbanned!')

@bot.command()
async def kick(ctx, reason: str = None):
    user = ctx.message.mentions
    for mention in user:
        await mention.kick(reason=reason)
        return await ctx.send('User has been kicked!')

@bot.command()
async def banuser(ctx, user, reason):
    if not user:
        return await ctx.send('Please provide a username to ban!')

    if not reason:
        return await ctx.send('You must provide a reason!')
    
    if not await check_link(ctx.author):
        return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')

    info = get_info(ctx.author)
    name = info[0]
    uid = info[1]

    info_ban = get_info_name(user)
    uid_ban = info_ban[0]
    if await check_link_id(uid_ban) is not False:
        discord = info_ban[1]
    else:
        discord = None

    await db.execute(f'UPDATE users SET priv = 2 WHERE id = {uid_ban}')
    await db.execute(f'INSERT INTO logs (from, to, msg, time) VALUES ({uid}, {uid_ban}, {reason}, NOW())')

    webhook_url = glob.config.webhook
    webhook = Webhook(url=webhook_url)
    embed = Embed(title = f'')
    embed.set_author(url = f"https://iteki.pw/u/{uid}", name = name, icon_url = f"https://a.iteki.pw/{uid}")
    embed.add_field(name = 'New banned user', value = f'{user} has been banned by {name} for {reason}.', inline = True)
    webhook.add_embed(embed)
    await webhook.post()

    if discord is not None:
        user = await bot.get_user(discord)
        try:
            await user.send_message(f'Your Iteki account has been banned for {reason}. If you believe this was in error, please contact @mbruhyo#8551.')
        except:
            print('Unable to message user, DMs are disabled.')

@bot.command()
async def unbanuser(ctx, user, reason):
    if not user:
        return await ctx.send('Please provide a username to unban!')

    if not reason:
        return await ctx.send('You must provide a reason!')
    
    if not await check_link(ctx.author):
        return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')

    info = get_info(ctx.author)
    name = info[0]
    uid = info[1]

    info_ban = get_info_name(user)
    uid_ban = info_ban[0]
    if await check_link_id(uid_ban) is not False:
        discord = info_ban[1]
    else:
        discord = None

    await db.execute(f'UPDATE users SET priv = 3 WHERE id = {uid_ban}')
    await db.execute(f'INSERT INTO logs (from, to, msg, time) VALUES ({uid}, {uid_ban}, f"Unbanned for {reason}", NOW())')

    webhook_url = glob.config.webhook
    webhook = Webhook(url=webhook_url)
    embed = Embed(title = f'')
    embed.set_author(url = f"https://iteki.pw/u/{uid}", name = name, icon_url = f"https://a.iteki.pw/{uid}")
    embed.add_field(name = 'New unbanned user', value = f'{user} has been unbanned by {name} for {reason}.', inline = True)
    webhook.add_embed(embed)
    await webhook.post()

    if discord is not None:
        user = await bot.get_user(discord)
        try:
            await user.send_message(f'Your Iteki account has been unbanned for {reason}.')
        except:
            print('Unable to message user, DMs are disabled.')


@bot.command()
async def minecraft(ctx):
        role = discord.utils.get(ctx.author.guild.roles, name=glob.config.mc_role)
        await ctx.author.add_roles(role)
        return await ctx.send('You now have the Minecraft role! You should be able to see the Minecraft section and you will now receive pings about the server.')

bot.run(glob.config.token)
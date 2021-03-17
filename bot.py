import cmyui
import glob
from cmyui.discord import Webhook, Embed
from discord.ext import commands
from PIL import Image
from enum import IntFlag, unique
import discord.utils
import discord
import random
import string
import aiohttp
import aiofiles
from resizeimage import resizeimage
from datetime import datetime, timedelta

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=glob.config.prefix, intents=intents)
db = cmyui.AsyncSQLPool()

async def get_info_id(user):
    e = await db.fetch(f'SELECT name FROM users WHERE id = {user}')
    f = await db.fetch(f'SELECT tag_id FROM discord WHERE user = {user}')
    try:
        discord = f['tag_id']
    except:
        discord = None
    return [e['name'], discord]

async def get_info(discord):
    f = await db.fetch(f'SELECT user FROM discord WHERE tag_id = {discord}')
    e = await db.fetch(f'SELECT name FROM users WHERE id = {f["user"]}')
    return [e['name'], f['user']]

async def get_info_name(user):
    e = await db.fetch(f'SELECT id FROM users WHERE safe_name = "{user.lower()}"')
    f = await db.fetch(f'SELECT tag_id FROM discord WHERE user = {e["id"]}')
    try:
        discord = f['tag_id']
    except:
        discord = None
    return [e['id'], discord]

async def check_link(discord):
    e = await db.fetch(f'SELECT user FROM discord WHERE tag_id = {discord}')
    try:
        return e['user']
    except:
        return False

async def check_link_id(user):
    e = await db.fetch(f'SELECT tag_id FROM discord WHERE user = {user}')
    try:
        return e['tag_id']
    except:
        return False

@bot.event
async def on_ready():
    await db.connect(glob.config.mysql)
    print('Bot started!')

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=glob.config.member_role)
    await member.add_roles(role)

@bot.command()
async def generate(ctx):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by, for_id) VALUES ("{key}", "{ctx.author}", 0)')
        await ctx.message.delete()
        return await ctx.author.send(f'Key generated!\n\nKey: `{key}`')
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def accept(ctx):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        mention = ctx.message.mentions
        await ctx.message.delete()
        for user in mention:
            key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
            await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by, for_id) VALUES ("{key}", "{ctx.author}", {user.id})')
            await user.send(f'Key generated!\n\nKey: `{key}`')
            role = discord.utils.get(user.guild.roles, name=glob.config.beta_role)
            return await user.add_roles(role)
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def avatar(ctx, url: str = None):
    if url is None:
        try:
            url = ctx.message.attachments[0].url
        except:
            return await ctx.send('Please ensure you provide either an image by URL or file upload! (Syntax: `!avatar <url if you are not using image upload>`)')
    if await check_link(ctx.author.id) is not False:
        a = await db.fetch(f'SELECT user FROM discord WHERE tag_id = {ctx.author.id}')
        uid = a['user']
    elif await check_link(ctx.author.id) == 1:
        return await ctx.send('You have already started the linking process, but have not finished it! Please check your DMs with me on Discord and follow the instructions to finish the linking process.')
    else:
        return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')
    async with aiohttp.ClientSession() as session:
        try:
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
                    return await ctx.send(f'Error getting image! If you provided a URL, please ensure that anyone has the permission to view this image and that the URL exists.')
        except:
            return await ctx.send(f'Error getting image! If you provided a URL, please ensure that anyone has the permission to view this image and that the URL exists.')

@bot.command()
async def link(ctx):
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    if await check_link(ctx.author.id) is False:
        try:
            await ctx.author.send(f'To finalise the linking process, please login ingame and send this command to Ruji:\n`!link {code}`')
            await ctx.send('Linking initiated! Please check your DMs for further instructions.')
            return await db.execute(f'INSERT INTO discord (tag, user, code, tag_id) VALUES ("{ctx.author}", 0, "{code}", {ctx.author.id})')
        except:
            return await ctx.send('I was unable to DM you instructions! Please ensure you have DMs enabled and try the command again.')
    elif await check_link(ctx.author.id) == 0:
        return await ctx.send(f'You have already started the linking process, but have not finished it! Please check your DMs with me on Discord and follow the instructions to finish the linking process.')
    else:
        return await ctx.send("Your Discord is already linked to an Iteki account! If you think this is in error, please DM @tsunyoku#8551 on Discord.")

@bot.command()
async def reg(ctx, code):
    checkc = await db.fetch('SELECT id, name FROM users WHERE code = %s', [code])
    if checkc is not None:
        await db.execute('UPDATE users SET verif = 1 WHERE id = %s', [checkc['id']])
        return await ctx.send(f"Thank you {checkc['name']} for verifying your account! Please attempt to login again.")
    else:
        return await ctx.send('Invalid code! Please double check the code and try again.')

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
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, reason=None):
    await member.ban(reason=reason)
    await ctx.send('User has been banned!')

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, member: discord.Member, reason=None):
    await member.unban(reason=reason)
    await ctx.send('User has been unbanned!')

@bot.command()
async def kick(ctx, reason: str = None):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        user = ctx.message.mentions
        for mention in user:
            await mention.kick(reason=reason)
            return await ctx.send('User has been kicked!')
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def banuser(ctx, user, reason):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        if not user:
            return await ctx.send('Please provide a username to ban!')

        if not reason:
            return await ctx.send('You must provide a reason!')
        
        if not await check_link(ctx.author.id):
            return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')

        info = await get_info(ctx.author.id)
        name = info[0]
        uid = info[1]

        info_ban = await get_info_name(user)
        uid_ban = info_ban[0]
        if await check_link_id(uid_ban) is not False:
            discord = info_ban[1]
        else:
            discord = None

        priv = await db.fetch(f'SELECT priv FROM users WHERE id = {uid_ban}')
        priv = int(priv['priv'])
        normal = 1 << 0
        priv &= ~normal
        await db.execute(f'UPDATE users SET priv = {priv} WHERE id = {uid_ban}')
        await db.execute(f'INSERT INTO logs (`from`, `to`, `msg`, `time`) VALUES ({uid}, {uid_ban}, "Banned for {reason}", NOW())')

        webhook_url = glob.config.webhook
        webhook = Webhook(url=webhook_url)
        embed = Embed(title = f'')
        embed.set_author(url = f"https://iteki.pw/u/{uid}", name = name, icon_url = f"https://a.iteki.pw/{uid}")
        embed.add_field(name = 'New banned user', value = f'{user} has been banned by {name} for {reason}.', inline = True)
        webhook.add_embed(embed)
        await webhook.post()
        await ctx.send(f'{user} has been banned!')

        if discord is not None:
            user = bot.get_user(discord)
            try:
                await user.send_message(f'Your Iteki account ({user}) has been banned for {reason}. If you believe this was in error, please contact @tsunyoku#8551.')
            except:
                print('Unable to message user, DMs are disabled.')
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def unbanuser(ctx, user, reason):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        if not user:
            return await ctx.send('Please provide a username to unban!')

        if not reason:
            return await ctx.send('You must provide a reason!')
        
        if not await check_link(ctx.author.id):
            return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')

        info = await get_info(ctx.author.id)
        name = info[0]
        uid = info[1]

        info_ban = await get_info_name(user)
        uid_ban = info_ban[0]
        if await check_link_id(uid_ban) is not False:
            discord = info_ban[1]
        else:
            discord = None

        priv = await db.fetch(f'SELECT priv FROM users WHERE id = {uid_ban}')
        priv = int(priv['priv'])
        normal = 1 << 0
        priv |= normal
        await db.execute(f'UPDATE users SET priv = {priv} WHERE id = {uid_ban}')
        await db.execute(f'INSERT INTO logs (`from`, `to`, `msg`, `time`) VALUES ({uid}, {uid_ban}, "Unbanned for {reason}", NOW())')

        webhook_url = glob.config.webhook
        webhook = Webhook(url=webhook_url)
        embed = Embed(title = f'')
        embed.set_author(url = f"https://iteki.pw/u/{uid}", name = name, icon_url = f"https://a.iteki.pw/{uid}")
        embed.add_field(name = 'New unbanned user', value = f'{user} has been unbanned by {name} for {reason}.', inline = True)
        webhook.add_embed(embed)
        await webhook.post()
        await ctx.send(f'{user} has been unbanned!')

        if discord is not None:
            user = bot.get_user(discord)
            try:
                await user.send_message(f'Your Iteki account ({user}) has been unbanned for {reason}!')
            except:
                print('Unable to message user, DMs are disabled.')
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def freezeuser(ctx, user, reason):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        if not user:
            return await ctx.send('Please provide a username to freeze!')

        if not reason:
            return await ctx.send('You must provide a reason!')
        
        if not await check_link(ctx.author.id):
            return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')

        info = await get_info(ctx.author.id)
        name = info[0]
        uid = info[1]

        info_ban = await get_info_name(user)
        uid_ban = info_ban[0]
        if await check_link_id(uid_ban) is not False:
            discord = info_ban[1]
        else:
            discord = None

        await db.execute(f'UPDATE users SET frozen = 1 WHERE id = {uid_ban}')
        freezedate = datetime.now() + timedelta(7)
        timer = freezedate.timestamp()
        await db.execute(f'UPDATE users SET freezetime = {timer} WHERE id = {uid_ban}')
        await db.execute(f'INSERT INTO logs (`from`, `to`, `msg`, `time`) VALUES ({uid}, {uid_ban}, "Frozen for {reason}", NOW())')

        webhook_url = glob.config.webhook
        webhook = Webhook(url=webhook_url)
        embed = Embed(title = f'')
        embed.set_author(url = f"https://iteki.pw/u/{uid}", name = name, icon_url = f"https://a.iteki.pw/{uid}")
        embed.add_field(name = 'New frozen user', value = f'{user} has been frozen by {name} for {reason}.', inline = True)
        webhook.add_embed(embed)
        await webhook.post()
        await ctx.send(f'{user} has been frozen!')

        if discord is not None:
            user = bot.get_user(discord)
            try:
                await user.send_message(f'Your Iteki account ({user}) has been frozen for {reason}! Please contact tsunyoku#8551 on Discord to be given a criteria you will be expected to liveplay to. You will be given 7 days to produce a liveplay or you will get autobanned.')
            except:
                print('Unable to message user, DMs are disabled.')
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def unfreezeuser(ctx, user):
    if ctx.author.top_role.id in (glob.config.admin_role_id, glob.config.dev_role_id, glob.config.owner_role_id):
        if not user:
            return await ctx.send('Please provide a username to unfreeze!')
        
        if not await check_link(ctx.author.id):
            return await ctx.send('Your Discord is not linked to any Iteki account! Please do `!link` to link your Iteki account and try again.')

        info = await get_info(ctx.author.id)
        name = info[0]
        uid = info[1]

        info_ban = await get_info_name(user)
        uid_ban = info_ban[0]
        if await check_link_id(uid_ban) is not False:
            discord = info_ban[1]
        else:
            discord = None

        await db.execute(f'UPDATE users SET frozen = 0 WHERE id = {uid_ban}')
        await db.execute(f'INSERT INTO logs (`from`, `to`, `msg`, `time`) VALUES ({uid}, {uid_ban}, "Unfrozen", NOW())')

        webhook_url = glob.config.webhook
        webhook = Webhook(url=webhook_url)
        embed = Embed(title = f'')
        embed.set_author(url = f"https://iteki.pw/u/{uid}", name = name, icon_url = f"https://a.iteki.pw/{uid}")
        embed.add_field(name = 'New unfrozen user', value = f'{user} has been unfrozen by {name}.', inline = True)
        webhook.add_embed(embed)
        await webhook.post()
        await ctx.send(f'{user} has been unfrozen!')

        if discord is not None:
            user = bot.get_user(discord)
            try:
                await user.send_message(f'Your Iteki account ({user}) has been unfrozen! Thank you for cooperating.')
            except:
                print('Unable to message user, DMs are disabled.')
    else:
        return await ctx.send("You don't have permissions to do that!")

@bot.command()
async def minecraft(ctx):
        role = discord.utils.get(ctx.author.guild.roles, name=glob.config.mc_role)
        await ctx.author.add_roles(role)
        return await ctx.send('You now have the Minecraft role! You should be able to see the Minecraft section and you will now receive pings about the server.')

bot.run(glob.config.token)
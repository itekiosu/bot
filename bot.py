import cmyui
import glob
import discord
import random
import string

class itekiBot(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def on_message(self, message):
        db = cmyui.AsyncSQLPool()
        await db.connect(glob.config.mysql)
        if message.author.id == self.user.id:
            return
        
        if message.content.startswith('!generate') and message.channel.id == glob.config.generate_channel:
            key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
            await db.execute(f'INSERT INTO beta_keys(beta_key, generated_by) VALUES ("{key}", "{message.author}")')
            await message.delete()
            return await message.author.send(f'Key generated!\n\nKey: `{key}`')

client = itekiBot()
client.run(glob.config.token)

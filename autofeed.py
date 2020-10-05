from discord.ext import tasks, commands
import discord
from datetime import datetime


class AutoFeedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('We have logged in as {0.user}'.format(self.bot))
        self.auto_feed.start()

    def cog_unload(self):
        self.auto_feed.cancel()

    @tasks.loop(seconds=10.0)
    async def auto_feed(self):
        # 時間になったら動作する
        dt = datetime.now()
        print(dt)
        channel: discord.TextChannel = self.bot.get_channel(751096956016918608)
        send_message: discord.Message = await channel.send(dt.strftime("%Y-%m-%d %H:%m:%d"))
        print(send_message.id)


import discord
import os
from discord.ext import commands
from manage_reaction import ManageReactionCog
from pprint import pprint

client = discord.Client()
# トークンを環境変数か.credentialsファイルから取得
TOKEN = os.environ.get("DISCORD_TOKEN", "")
if TOKEN == "":
    with open(".credentials", "r") as f:
        TOKEN = f.read().strip()

bot = commands.Bot(command_prefix='t!')
bot.add_cog(ManageReactionCog(bot))
bot.run(TOKEN)

import discord
from discord.ext import commands
from manage_reaction import ManageReactionCog

client = discord.Client()
TOKEN = 'Your Token'


bot = commands.Bot(command_prefix='t!')
bot.add_cog(ManageReactionCog(bot))
bot.run(TOKEN)

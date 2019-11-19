import discord
from discord.ext import commands
from .config import *
import re
import random
import asyncio

class Dev(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def is_dev(ctx): # Can't pass self into this for some reason, so doing it the hard way
		THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

		with open(os.path.join(THIS_FOLDER, '..', 'owner_id.txt')) as fh:
			owner_id = int(fh.readline())

		if (ctx.message.author.id == owner_id):
			return True

	# View servers the bot is in
	@commands.command(name="servers")
	@commands.check(is_dev)
	async def servers(self, ctx):
		guilds = self.bot.guilds

		guild_str = ''

		all_members = [];

		for guild in guilds:
			guild_str += f"{guild}\n"
			
			guild_members = guild.members
			member_ids = [member.id for member in guild_members]
			all_members.extend(member_ids)

		embed = discord.Embed(title="List of Servers I am in:", description=guild_str[0:1999])
		embed.add_field(name="Unique users", value=f"{len(set(all_members))}")
		
		# Get number of unique users across guilds
		await ctx.send(embed=embed)

	# Dev command to do whatever
	@commands.command(name="dev")
	@commands.check(is_dev)
	async def dev(self, ctx):
		await ctx.send("dev command works")

def setup(bot):
	bot.add_cog(Dev(bot))

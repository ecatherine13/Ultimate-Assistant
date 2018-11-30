import discord
from discord.ext import commands
from .config import *
import re
import random

class Memes:
	def __init__(self, bot):
		self.bot = bot

	# Hunger Games :deflate"
	@commands.command(name="hunger_games", aliases=["hg"], help="Randomized KG sim a la Hunger Games Sim")
	async def hunger_games(self, ctx):
		await ctx.send("In progress")

def setup(bot):
	bot.add_cog(Memes(bot))
import discord
from discord.ext import commands
import sqlite3
from sqlite3 import Error
import random
import os
import asyncio
import time
import sys, traceback
from cogs import config
import json
from cogs.config import *

def main():

	def prefix(bot, msg):
		guild_id = msg.guild.id
		cs.execute(f"SELECT Prefix FROM GuildData WHERE GuildID == {guild_id} LIMIT 1")

		prefix = cs.fetchone()[0]

		if (prefix == None):
			prefix = "!"

		return prefix

	bot = commands.Bot(command_prefix=prefix, description="A bot for Danganronpa RP! Use `!src` to see full documentation~")

###################################################################################	
# Load cogs

	initial_extensions =	[
							"cogs.utility",
							"cogs.events",
							"cogs.admin", 
							"cogs.management", 
							"cogs.inventory", 
							# "cogs.memes", 
							"cogs.announcements", 
							"cogs.gacha", 
							"cogs.investigation", 
							"cogs.maps", 
							"cogs.dev", 
							"cogs.dice"
						  	]

	if __name__ == "__main__":
	    for extension in initial_extensions:
	        try:
	            bot.load_extension(extension)
	            print(f"Loaded {extension}")
	        except Exception as e:
	            print(f"Failed to load extension {extension}.", file=sys.stderr)
	            traceback.print_exc()

###################################################################################	
# Events
	
	@bot.event
	async def on_command_error(ctx, error):
		if isinstance(error, commands.CommandNotFound):
			pass
			
		elif isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Missing an argument! Use `!help <command name>`")
		
		elif isinstance(error, commands.MissingPermissions):
			await ctx.send(f"You do not have permissions to use this command!")
		
		elif isinstance(error, commands.BotMissingPermissions):
			await ctx.send("My highest role does not have permissions to use this command!")

		elif isinstance(error, commands.CommandOnCooldown):
			await ctx.send(error)

		else:
			guild_id = ctx.guild.id
			channel_id = ctx.message.channel.id
			user_id = ctx.message.author.id
			message = ctx.message.content

			error_message = f"**[ERROR]** \n**GuildID**: {guild_id} \n**ChannelID**: {channel_id} \n**UserID**: {user_id} \n**Command Attempted**: {message} \n**ErrorType**: {type(error)} \n**Error**: {error}\n--------------------------------------------"

			# DM error message to bot owner
			user = bot.get_user(owner_id)
			await user.send(error_message)

			# Notify user
			msg = await ctx.send("Whoops, something went wrong! An error report has been sent to the developer. Read the documentation with `!src`, or bring your question to the development server (invite in readme)")
			await asyncio.sleep(8)
			await msg.delete()
###################################################################################	
# Run bot	

	with open('token.txt') as fh:
		token = fh.readline()

	with open('owner_id.txt') as fh:
		owner_id = int(fh.readline())
	
	random.seed(time.time())
	
	bot.run(str(token))

	# Close database
	config.close_connection()

def scratchwork():
	# :) Testing dev branch commit/push
	return 0

main()
# scratchwork()

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

def main():
	
	bot = commands.Bot(command_prefix="$", description="A bot I threw together")

###################################################################################	
# Load cogs

	initial_extensions =	[
							"cogs.utility",
							"cogs.events",
							"cogs.admin", 
							"cogs.management", 
							"cogs.inventory", 
							"cogs.memes", 
							"cogs.announcements", 
							"cogs.gacha", 
							"cogs.investigation", 
							"cogs.maps"
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
			await ctx.send(f"That is not a command! Use `!help` for a list.")
		
		elif isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Missing an argument! Use `!help <command name>`")
		
		elif isinstance(error, commands.MissingPermissions):
			await ctx.send(f"You do not have permissions to use this command!")
		
		elif isinstance(error, commands.BotMissingPermissions):
			await ctx.send("My highest role does not have permissions to use this command!")
		
		else:
			guild_id = ctx.guild.id
			channel_id = ctx.message.channel.id
			user_id = ctx.message.author.id
			message = ctx.message.content

			error_message = f"**[ERROR]** \n**GuildID**: {guild_id} \n**ChannelID**: {channel_id} \n**UserID**: {user_id} \n**Command Attempted**: {message} \n**ErrorType**: {type(error)} \n**Error**: {error}"

			# DM error message to bot owner
			user = bot.get_user(owner_id)
			await user.send(error_message)

			# Notify user
			await ctx.send("Whoops! Something went wrong. Reminder that the timeout for all inputs is 60 s. An error report has been sent to the developer.")

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
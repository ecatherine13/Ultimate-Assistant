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
import datetime

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
							# "cogs.events",
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
	
	@bot.event
	async def on_ready():
		
		print("Here")
		# Correct announcements that have passed without posting (post times during bot downtime)
		time_now = datetime.datetime.utcnow()
		int_timestamp_now = int(time_now.strftime("%Y%m%d%H%M"))

		cs.execute(f"SELECT Frequency, NextPosting, GuildID, ChannelID FROM Announcements WHERE Frequency > 0 AND Frequency < 100000 AND NextPosting < {int_timestamp_now}")
		passed_announcements = cs.fetchall()

		# There's probably a nicer and faster way to do this, but for now, just loop.
		for announcement in passed_announcements:
			frequency = announcement[0]
			passed_time = datetime.datetime.strptime(str(announcement[1]), "%Y%m%d%H%M")

			while (passed_time < time_now):
				passed_time = passed_time + datetime.timedelta(hours=frequency)

			passed_time_int = int(passed_time.strftime("%Y%m%d%H%M"))

			cs.execute(f"UPDATE Announcements SET NextPosting = {passed_time_int} WHERE GuildID == {announcement[2]} AND ChannelID == {announcement[3]} AND NextPosting == {announcement[1]} AND Frequency == {frequency} LIMIT 1")
			conn.commit()

		print("\nSynced Announcements")

		# Add guild entries to GuildData if bot was added while offline, also weed out guilds it's been kicked out of (TODO)
		bot_guild_ids = [x.id for x in bot.guilds]

		# If guild not in DB, add to it
		for guild_id in bot_guild_ids:
			cs.execute(f"SELECT 1 FROM GuildData WHERE GuildID == {guild_id} LIMIT 1")
			guild_in_db = cs.fetchone() is not None
			
			if(guild_in_db == False):
				cs.execute(f"INSERT INTO GuildData (GuildID) VALUES ({guild_id})")
				conn.commit()

		print("Synced Guilds")

		# Check Investigations and Maps for deleted Channels, Roles etc.
		# Investigations
		# cs.execute(f"SELECT DISTINCT ChannelID FROM Investigations")

		# for channel_id_entry in cs.fetchall():
		# 	channel_id = channel_id_entry[0]
		# 	channel_obj = bot.get_channel(channel_id)

		# 	if (channel_obj == None):
		# 		# Remove the entries
		# 		cs.execute(f"DELETE FROM Investigations WHERE ChannelID == {channel_id}")

		# conn.commit()
		# print("Synced Investigations")

		# Maps. Check for deleted channel or role
		# cs.execute(f"SELECT ChannelID, RoleID FROM Maps")
		# conns_to_remove = []
		# for channel_entry in cs.fetchall():
		# 	channel_id = channel_entry[0]
		# 	role_id = channel_entry[1]

		# 	channel_obj = bot.get_channel(channel_id)

		# 	try:
		# 		role_obj = channel_obj.guild.get_role(role_id)
		# 	except:
		# 		role_obj = None

		# 	if (channel_obj == None or role_obj == None):
		# 		cs.execute(f"DELETE FROM Maps WHERE ChannelID == {channel_id} LIMIT 1")
		# 		conns_to_remove.append(channel_id)

		# conn.commit()

		# Remove connections. Inefficient as hell but it only happens once per bot login. 
		# cs.execute(f"SELECT ChannelID, OutgoingConnections FROM Maps")
		# all_channels_entry = cs.fetchall()

		# for channel_entry in all_channels_entry:
		# 	outgoing_conns_str = channel_entry[1]
		# 	channel_id = channel_entry[0]

		# 	conns = json.loads(outgoing_conns_str)

		# 	# Remove the intersection of conns_to_remove and conns from conns
		# 	conns = [x for x in conns if x not in conns_to_remove]

		# 	new_conns_str = str(json.dumps(conns))

		# 	cs.execute(f"UPDATE Maps SET OutgoingConnections = ? WHERE ChannelID == {channel_id} LIMIT 1", (f"{new_conns_str}",))

		# conn.commit()
		# print("Synced Maps")

		print(f"\nLogged in as {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n")
		await bot.change_presence(activity=discord.Game(name='!help'))

		bot.loop.create_task(announcement_task())
	
	@bot.event
	async def on_guild_join(ctx):
		guild_id = ctx.id

		# If guild not in DB, add to it
		cs.execute(f"SELECT 1 FROM GuildData WHERE GuildID == {guild_id} LIMIT 1")
		guild_in_db = cs.fetchone() is not None
		
		if(guild_in_db == False):
			cs.execute(f"INSERT INTO GuildData (GuildID) VALUES ({guild_id})")
			conn.commit()
	
	@bot.event
	async def on_member_join(ctx): # ctx is the Member
		guild_id = ctx.guild.id

		# Assign autorole if one is set up
		role_cs = cs.execute(f"SELECT AutoRole FROM GuildData WHERE GuildID={ctx.guild.id} LIMIT 1")
		
		try:
			role_id = role_cs.fetchone()[0]
		except:
			role_id = None

		if(role_id != None):
			role = discord.utils.get(ctx.guild.roles, id=role_id)
			await ctx.add_roles(role)
	
	@bot.event
	async def on_member_remove(ctx):
		# TODO - Remove from User table?
		return 0
	
	@bot.event
	async def on_guild_remove(ctx):
		# Remove guild specific things from announcements, investigations, gacha, and user data but leave characters for now.

		# GuildData TODO

		# Remove announcements
		cs.execute(f"DELETE FROM Announcements WHERE GuildID == {ctx.id}")

		# Remove Investigations
		cs.execute(f"DELETE FROM Investigations WHERE GuildID == {ctx.id}")

		# Remove Gacha
		cs.execute(f"DELETE FROM Gacha WHERE GuildID == {ctx.id}")

		# Remove user data
		cs.execute(f"DELETE FROM UserData WHERE GuildID == {ctx.id}")

		conn.commit()

	@bot.event
	async def on_guild_role_delete(ctx): # ctx is Role
		
		# Check if role was a channel role
		cs.execute(f"SELECT ChannelID FROM Maps WHERE RoleID == {ctx.id} LIMIT 1")
		channel_id_entry = cs.fetchone()
		if channel_id_entry is not None: # in db, delete entry and remove connections
			channel_id = channel_id_entry[0]

			# Delete Entry
			cs.execute(f"DELETE FROM Maps WHERE ChannelID == {channel_id} LIMIT 1")
			conn.commit()

			# Delete connections to channel_id
			cs.execute(f"SELECT OutgoingConnections, ChannelID FROM Maps WHERE GuildID == {ctx.guild.id}")

			all_connections_str = cs.fetchall()

			for conn_str in all_connections_str:
				conns = json.loads(conn_str[0])
				conn_channel_id = conn_str[1]

				if (channel_id in conns):
					conns = [x for x in conns if x != channel_id]

					new_conns_str = str(json.dumps(conns))

					# Commit
					cs.execute(f"UPDATE Maps SET OutgoingConnections = ? WHERE ChannelID == {conn_channel_id} LIMIT 1", (f"{new_conns_str}",))

			conn.commit()
	
	@bot.event
	async def on_guild_channel_delete(ctx): #ctx is Channel

		# Check if channel was in Maps
		cs.execute(f"SELECT 1 FROM Maps WHERE ChannelID == {ctx.id} LIMIT 1")

		channel_in_maps = cs.fetchone() is not None

		if (channel_in_maps):
			channel_id = ctx.id
			# Remove the entry
			cs.execute(f"DELETE FROM Maps WHERE ChannelID == {channel_id} LIMIT 1")

			# Remove connections
			cs.execute(f"SELECT OutgoingConnections, ChannelID FROM Maps WHERE GuildID == {ctx.guild.id}")

			all_connections_str = cs.fetchall()

			for conn_str in all_connections_str:
				conns = json.loads(conn_str[0])
				conn_channel_id = conn_str[1]

				if (channel_id in conns):
					conns = [x for x in conns if x != channel_id]

					new_conns_str = str(json.dumps(conns))

					# Commit
					cs.execute(f"UPDATE Maps SET OutgoingConnections = ? WHERE ChannelID == {conn_channel_id} LIMIT 1", (f"{new_conns_str}",))

			conn.commit()

		# TODO Check if channel was in investigations or announcements

	# Announcement background task
	# TODO Allow for time pauses
	async def announcement_task():
		in_sync = False # Changes to true on the first half hour available
		while (True):
			time_now = datetime.datetime.utcnow()

			# Syncing
			if (not in_sync):
				if(time_now.minute == 0 or time_now.minute == 30):
					in_sync = True
				else:
					await asyncio.sleep(15) # Check every 15 seconds

			# Synced
			if (in_sync):
				time_now_int = int(time_now.strftime("%Y%m%d%H%M"))

				# Correct desynced time due to lag and set as not in sync
				if (time_now.minute != 30 or time_now.minute != 0):
					if (15 <= time_now.minute and time_now.minute <= 44): # 30
						time_now_int = time_now_int - (time_now_int % 100) + 30
					else:
						time_now_int = time_now_int - (time_now_int % 100)

					in_sync = False # resync

				# Get announcements
				cs.execute(f"SELECT * FROM Announcements WHERE NextPosting == {time_now_int}")
				announcements = cs.fetchall()

				# Post announcements
				for announcement in announcements:
					guild_id = announcement[0]
					channel_id = announcement[1] # Channel IDs are guaranteed unique globally
					message = announcement[2]
					frequency = announcement[3]
					current_posting = announcement[4]

					# Send message

					try:
						channel = bot.get_channel(channel_id)
						await channel.send(message)
					except: # Channel nonexistent or lacked permissions. TODO Better handling
						pass

					# Update next posting
					current_posting_datetime = datetime.datetime.strptime(str(current_posting), "%Y%m%d%H%M")	
					next_posting = current_posting_datetime + datetime.timedelta(hours=frequency)
					next_posting = int(next_posting.strftime("%Y%m%d%H%M"))

					# Update entry
					cs.execute(f"UPDATE Announcements SET NextPosting = {next_posting} WHERE GuildID == {guild_id} AND ChannelID == {channel_id} AND Message = ?", (message,))
					conn.commit()

				# if still in sync
				if (in_sync):
					await asyncio.sleep(1800) # 30 minutes
				else: # out of sync
					await asyncio.sleep(15)
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

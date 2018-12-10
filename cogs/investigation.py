import discord
from discord.ext import commands
from .config import *
import re
import random
import json
import itertools
import operator

class Investigation:
	def __init__(self, bot):
		self.bot = bot

	# Embed intestigatable items. One embed per channel
	def embed_investigation(self, guild_id):
		cs.execute(f"SELECT ChannelID, ItemNames, ItemInfo FROM Investigations WHERE GuildID == {guild_id}")

		all_objects = cs.fetchall()

		# Sort list of tuples by channel
		all_objects.sort(key=lambda tup: tup[0])

		# for object_str in all_objects:
		# 	print(object_str)
		embeds = []
		idx = 0
		for key,group in itertools.groupby(all_objects, operator.itemgetter(0)): #grouped by channel id
			
			channel_objects = list(group)
			channel_id = channel_objects[0][0]

			channel = self.bot.get_channel(channel_id)

			embed = discord.Embed(title=f"Investigatable objects in #{channel}")

			for obj in channel_objects:
				item_names = obj[1]
				item_description = obj[2]

				embed.add_field(name=f"[{idx}] {item_names}", value=item_description, inline=False)
				idx += 1

			embeds.append(embed)

		return embeds

	# New investigatable item. 
	@commands.command(name="new_investigation", aliases=["newinvestigation", "ninv"], help="Add a new investigatable item/object. Requires channel tag.")
	@commands.has_permissions(administrator=True)
	async def new_investigation(self, ctx, channel):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		# To avoid tons of nested try staatements, use a continue value
		cont = True

		# Make sure it's a proper channel
		# obtains int channel_id
		if(cont):
			# Capture channel id
			regex = "<#([0-9]{18})>"
			channel_id_str = re.findall(regex, channel)

			try:
				channel_id = int(channel_id_str[0])

			except:
				await ctx.send("That is not a proper channel! Please use `#channel-name` with the tag.")
				cont = False

		# Allow 25 objects per channel, because embed limit and just being reasonable
		if (cont):
			# Get all ItemNames for channelID
			cs.execute(f"SELECT ItemNames FROM Investigations WHERE ChannelID == {channel_id}")
			all_names_strs = cs.fetchall()

			if (len(all_names_strs) > 25):
				await ctx.send("You may only have a maximum of 25 objects per channel!")
				cont = False

		# Get list of names. Check for no repeats
		if (cont):
			await ctx.send("Enter a name for the object, or a comma separated list. (ex. 'curtain, curtains, blue curtains')")
			names = await self.bot.wait_for('message', check=pred, timeout=60)
			names = names.content.lower()
			names = [x.strip() for x in names.split(',')] # returns array of strings
			
			# Now check that the channel doesn't have any repeated object names
			for name_strs in all_names_strs:
				names_json = json.loads(name_strs[0])

				# intersection of the two sets names and names_json
				set_names = set(names)
				set_existing_names = set(names_json)
				if(len(set_names.intersection(set_existing_names)) != 0):
					await ctx.send(f"At least one of those object names is already in use in {channel}!")
					cont = False
					break

		# Get object description
		if (cont):
			await ctx.send("Enter a description for the object.")
			description = await self.bot.wait_for('message', check=pred, timeout=60)
			description = description.content

		# Add to db
		if (cont):
			guild_id = ctx.guild.id
			names = json.dumps(names)

			cs.execute(f"INSERT INTO Investigations (GuildID, ChannelID, ItemNames, ItemInfo) VALUES ({guild_id}, {channel_id}, ?, ?)", (f"{names}", f"{description}"))
			conn.commit()

			await ctx.send(f"Set up investigation object in {channel}!")

	# Delete one or more investigatable objects
	@commands.command(name="rem_investigation", aliases=["reminvestigation", "rinv"], help="Remove one or more investigatable items/objects")
	@commands.has_permissions(administrator=True)
	async def rem_investigation(self, ctx):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		# Display objects
		embeds = self.embed_investigation(ctx.guild.id)

		if (len(embeds) == 0):
			await ctx.send("No investigations set up!")
		else:
			for embed in embeds:
				await ctx.send(embed=embed)

		# Get list in appropriate order
		cs.execute(f"SELECT ChannelID, ItemNames, ItemInfo FROM Investigations WHERE GuildID == {ctx.guild.id}")

		all_objects = cs.fetchall()

		# Sort list of tuples by channel
		all_objects.sort(key=lambda tup: tup[0])

		# Get input and delete corresponding items
		await ctx.send("Enter a number, or a list of comma separated numbers: (ex. 1, 3, 10) \nEnter 'X' to exit without deleting.")
		entry = await self.bot.wait_for('message', check=pred, timeout=60)
		entry = entry.content
		idx_to_delete_strs = entry.split(',')

		for idx_str in idx_to_delete_strs:

			cont = True

			# Exit if idx_str.upper() == 'X'
			if (idx_str.upper() == 'X'):
				await ctx.send("Exiting!")
				cont = False
				break

			# Typecast to int will fail if it's not a number
			try:
				idx_to_delete = int(idx_str)

				# If that works, warn about numbers not in range (up to idx because exit option)
				if (0 > idx_to_delete or len(all_objects) < idx_to_delete):
					await ctx.send(f"{idx_to_delete} is not within the given range!")
					cont = False

			except:
				await ctx.send(f"{idx_str} is not a valid number!")
				cont = False

			# If those both check out, delete
			if (cont):
				item_to_delete = all_objects[idx_to_delete]

				cs.execute(f"DELETE FROM Investigations WHERE GuildID == {ctx.guild.id} AND ChannelID = {all_objects[idx_to_delete][0]} AND ItemNames == ?", (f"{item_to_delete[1]}",))

				conn.commit()

				await ctx.send(f"{item_to_delete[1]} deleted from investigations!")

	# View the investigations
	@commands.command(name="investigations", help="View all investigatable objects set up.")
	@commands.has_permissions(administrator=True)
	async def investigations(self, ctx):
		# Display objects
		embeds = self.embed_investigation(ctx.guild.id)

		if (len(embeds) == 0):
			await ctx.send("No investigations set up!")
		else:
			for embed in embeds:
				await ctx.send(embed=embed)

	# Command to actually investigate. DMs the description. The command must be done in the channel of investigation.
	@commands.command(name="investigate", aliases=["check"], help="Investigate in a channel! Secret investigations can be done using !rinvestigate.")
	async def investigate(self, ctx, *, obj_name):

		cont = True

		guild_id = ctx.guild.id
		player_id = ctx.message.author.id

		# Check that the user is a player
		cs.execute(f"SELECT PlayingAs from UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")
		try:
			has_char = cs.fetchone()[0] is not None

			if(has_char == False):
				await ctx.send("You must be a player to investigate!")
				cont = False
		except TypeError:
			await ctx.send("You must be a player to investigate!")
			cont = False

		if (cont):
			channel_id = ctx.message.channel.id

			cs.execute(f"SELECT ItemNames, ItemInfo, Found FROM Investigations WHERE ChannelID == {channel_id}")

			channel_objects_strs = cs.fetchall()

			success = False
			# Check the item names
			for obj_str in channel_objects_strs:
				obj_names = json.loads(obj_str[0])
				if obj_name.lower() in obj_names:
					
					user = self.bot.get_user(player_id)
					await user.send(f"**{obj_name.upper()}** \n{obj_str[1]}")
					success = True

					# If user was first to find it, note it
					if obj_str[2] == 0: # First
						cs.execute(f"UPDATE Investigations ")

					break

			if (not success):
				user = self.bot.get_user(player_id)
				await user.send(f"You do not find anything of note!")

	# Command to investigate. DMs the description. The command can be done outside of a channel to keep it secret. This command could go in with the regular investigation, but the argument order made it annoying.
	@commands.command(name="rinvestigate", aliases=["rcheck", "remote_investigate", "remoteinvestigate"], help="Investigate in a channel remotely.")
	async def rinvestigate(self, ctx, channel, *, obj_name):

		cont = True

		guild_id = ctx.guild.id
		player_id = ctx.message.author.id

		# Check that the user is a player
		cs.execute(f"SELECT PlayingAs from UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")
		has_char = cs.fetchone()[0] is not None
			
		if(has_char == False):
			await ctx.send("You must be a player to investigate!")
			cont = False

		# Chek validity of channel name
		if (cont):
			regex = "<#([0-9]{18})>"
			channel_id_str = re.findall(regex, channel)

			try:
				channel_id = int(channel_id_str[0])
			except:
				await ctx.send("That is not a proper channel! Please use `#channel-name` with the tag.")
				cont = False
		
		if (cont):
			cs.execute(f"SELECT ItemNames, ItemInfo FROM Investigations WHERE ChannelID == {channel_id}")

			channel_objects_strs = cs.fetchall()

			success = False
			# Check the item names
			for obj_str in channel_objects_strs:
				obj_names = json.loads(obj_str[0])
				if obj_name.lower() in obj_names:
					# TODO DM
					user = self.bot.get_user(player_id)
					await user.send(f"**{obj_name.upper()}** \n{obj_str[1]}")
					success = True
					break

			if (not success):
				user = self.bot.get_user(player_id)
				await user.send(f"You do not find anything of note!")

	# TODO Remote investigation, for secret investigations. Requires the channel tag as an argument. This could easily go in the previous command but the argument order would be kinda annoying.

def setup(bot):
	bot.add_cog(Investigation(bot))
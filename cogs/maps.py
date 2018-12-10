import discord
from discord.ext import commands
from .config import *
import re
import random
import json

class Maps:
	def __init__(self, bot):
		self.bot = bot

	def is_channel(self, msg):
		regex = "<#([0-9]{18})>"
		channel_id_str = re.findall(regex, msg)

		try:
			channel_id = int(channel_id_str[0])
			return channel_id

		except:
			return False
	
	# Set up a role that gives view/send/history perms to given channel
	@commands.command(name="new_area_role", aliases=["nar", "newarearole"], help="Creates a role that grants read/send/history perms to given channel.")
	@commands.has_permissions(administrator=True)
	async def new_area_role(self, ctx, channel):

		cont = True
		
		# Make sure it's a proper channel
		# obtains Channel channel_obj
		channel_id = self.is_channel(channel)
		if (not channel_id):
			await ctx.send(f"That is not a proper channel!")
			cont = False
		else:
			channel_obj = self.bot.get_channel(channel_id)

		# If the channel is already in the db, display error message
		if (cont):
			cs.execute(f"SELECT 1 FROM Maps WHERE ChannelID == {channel_id} LIMIT 1")

			ch_in_db = cs.fetchone() is not None

			if(ch_in_db):
				await ctx.send(f"{channel} is already set up! To modify connections, use `!ac #{channel_obj.name}`.")
				cont = False
			else: # add the entry and role
				channel_name = channel_obj.name
				new_role = await ctx.guild.create_role(name=channel_name)

				# Set channel perms for role
				await channel_obj.set_permissions(new_role, read_messages=True, send_messages=True, read_message_history=True)

				# Entry
				cs.execute(f"INSERT INTO Maps (GuildID, ChannelID, RoleID) VALUES ({ctx.guild.id}, {channel_id}, {new_role.id})")
				conn.commit()

				await ctx.send(f"Set up role for {channel}, use `!ac #{channel_obj.name}` to add connections.")

	# Edit connections
	@commands.command(name="set_connections", aliases=["map_connections", "mapconnections", "sc"], help="Set channel connections for a channel-specific role. CThere's currently no way to edit an existing list of connections, but it can be overwritten at any time.")
	@commands.has_permissions(administrator=True)
	async def set_connections(self, ctx, *, channel):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		cont = True

		channel_id = self.is_channel(channel)
		if (not channel_id):
			channel_id = await ctx.send("That is not a valid channel! Remember to tag it.")
			cont = False

		# Check if it's in db
		# Gets channel_obj and outgoing_channel_ids
		if (cont):
			channel_obj = self.bot.get_channel(channel_id)
			cs.execute(f"SELECT OutgoingConnections FROM Maps WHERE ChannelID == {channel_id} LIMIT 1")
			
			try:
				outgoing_channel_ids = json.loads(cs.fetchone()[0]) # list
			except:
				await ctx.send(f"You haven't set that channel up yet! use `!nar #{channel_obj.name}`")
				cont = False
			
		# Ask for list of channels that lead to destination. If none (can be accessed from any channel), enter 'X'
		if (cont):
			valid_channels = []
			await ctx.send(f"Enter a channel, or comma separated list of outgoing channels from {channel}. If none, enter 'X'.")

			outgoing_channels = await self.bot.wait_for('message', check=pred, timeout=60)
			outgoing_channels = [x.strip() for x in outgoing_channels.content.split(',')]
			
			for channel in outgoing_channels:
				if(channel.lower() == 'x'):
					await ctx.send("Exiting without adding any connections.")
					cont = False
					break
				
				outgoing_channel_id = self.is_channel(channel)
				if (outgoing_channel_id):
					valid_channels.append(outgoing_channel_id)
				else:
					await ctx.send(f"{channel} is not a valid channel!")

		# If not empty, valid_channels to json str. Add to db
		if (len(valid_channels) > 0 and cont):
			valid_channels_str = str(json.dumps(valid_channels))
			cs.execute(f"UPDATE Maps SET OutgoingConnections = ? WHERE ChannelID == {channel_id} LIMIT 1", (f"{valid_channels_str}",))
			conn.commit()
		
		# Loop through valid connections and set them. Add nonexistent channels to db and confirm two-way connections.
		if (cont):
			for outgoing_channel_id in valid_channels:
				cs.execute(f"SELECT 1 from Maps WHERE ChannelID == {outgoing_channel_id} LIMIT 1")

				ch_in_db = cs.fetchone() is not None

				outgoing_channel_obj = self.bot.get_channel(outgoing_channel_id)
				
				# Add outgoing channel to db if DNE
				if(not ch_in_db):
					outgoing_channel_name = outgoing_channel_obj.name
					new_role = await ctx.guild.create_role(name=outgoing_channel_name)

					# TODO - Set channel perms for new role
					await outgoing_channel_obj.set_permissions(new_role, read_messages=True, send_messages=True, read_message_history=True)

					# Entry
					cs.execute(f"INSERT INTO Maps (GuildID, ChannelID, RoleID) VALUES ({ctx.guild.id}, {outgoing_channel_id}, {new_role.id})")
					conn.commit()

					await ctx.send(f"Role for {outgoing_channel_obj} added.")

				# Ask if the connection is two-way
				await ctx.send(f"Connected #{channel_obj} -> #{outgoing_channel_obj}. Is this a two way connection? (y/n)")
				response = await self.bot.wait_for('message', check=pred, timeout=60)

				if (response.content.lower() == 'y' or response.content.lower() == 'yes'):
					cs.execute(f"SELECT OutgoingConnections from Maps WHERE ChannelID == {outgoing_channel_id} LIMIT 1")
					connections = json.loads(cs.fetchone()[0])

					if (channel_id not in connections):
						connections.append(channel_id)

					cs.execute(f"UPDATE Maps SET OutgoingConnections = ? WHERE ChannelID == {outgoing_channel_id} LIMIT 1", (f"{connections}",))
					conn.commit()

					await ctx.send(f"Connected #{outgoing_channel_obj} -> #{channel_obj}.")

				elif (response.content.lower() == 'n' or response.content.lower() == 'no'):
					await ctx.send(f"Not connecting #{outgoing_channel_obj} -> #{channel_obj}")
					continue
				else:
					await ctx.send("Invalid input. Defaulting to 'N'.")

		# Finish
		if (cont):
			await ctx.send("Finished setting connections.")

	# View 'map' of connections in server
	@commands.has_permissions(administrator=True)
	@commands.command(name="map", aliases=["connections", "view_connections"], help="View channel connections for server.")
	async def map(self, ctx):
		cs.execute(f"SELECT ChannelID, OutgoingConnections FROM Maps WHERE GuildID == {ctx.guild.id}")
		channel_map = cs.fetchall()

		embed_0 = discord.Embed(title=f"Channel Connections for {ctx.guild} (all outgoing)")

		embeds = [embed_0]
		
		i = 0 # embeds index
		n = 0 # channel number
	
		for channel in channel_map:
			channel_id = channel[0]
			channel_obj = self.bot.get_channel(channel_id)
			channel_connections = json.loads(channel[1])
			connections_str = ''

			# Build string
			for connection in channel_connections:
				connection_obj = self.bot.get_channel(connection)
				connections_str += f"{connection_obj.name}\n"

			# Add to embed
			if (connections_str != ''):
				embeds[i].add_field(name=channel_obj.name, value=connections_str)
			else:
				embeds[i].add_field(name=channel_obj.name, value="-")
			n += 1

			if (n == 25):
				n = 0
				embed_n = discord.Embed()
				embeds.append(embed_n)
				i += 1

		# Send embeds
		for embed in embeds:
			await ctx.send(embed=embed)

	# Commend to move to an area on the map. Checks if the destination is in OutgoingConnections for currently held roles. 
	@commands.command(name="go", aliases=["goto", "move", "moveto"], help="Move to a new area that's listed in the server's Map. Checks if user is a player with a character.")
	async def go(self, ctx, channel_name):
		cont = True

		# Check if user is a player
		if (cont):
			cs.execute(f"SELECT PlayingAs FROM UserData WHERE GuildID == {ctx.guild.id} AND UserID == {ctx.message.author.id} LIMIT 1")

			try:
				is_player = cs.fetchone()[0] is not None
			except TypeError:
				is_player = False

			if not (is_player):
				await ctx.send(f"You are not a player on {ctx.guild}!")
				cont = False

		# Check if channel_name is valid
		# Obtains Channel object channel
		if (cont):
			destination_channel = discord.utils.get(ctx.guild.text_channels, name=channel_name.lower())
			if (destination_channel == None):
				await ctx.send("That is not a valid channel name!")
				cont = False

		# Get relevant map info and check if user is in a connecting area
		if (cont):
			cs.execute(f"SELECT RoleID FROM Maps WHERE GuildID == {ctx.guild.id}")
			channel_map = cs.fetchall()

			role_ids = [x[0] for x in channel_map]
			user_roles = [x.id for x in ctx.message.author.roles]

			intersection = list(set(role_ids) & set(user_roles))
			
			if (len(intersection) == 0):
				await ctx.send(f"You are not in a connected area!")
				cont = False
			else:
				current_role_id = intersection[0]

				cs.execute(f"SELECT OutgoingConnections FROM Maps WHERE RoleID == {current_role_id} LIMIT 1") # Roles are snowflakes

				outgoing_connections = json.loads(cs.fetchone()[0])

		#Check if destination channel_id is in outgoing connections
		if (cont):
			if (destination_channel.id not in outgoing_connections):
				await ctx.send(f"You are not in an area that connects to #{destination_channel}!")

			else: # switch out the roles.
				# Remove the intersection role. If done right, it should only be one.
				role_to_remove = ctx.guild.get_role(current_role_id)

				# Get role id for destination channel
				cs.execute(f"SELECT RoleID FROM Maps WHERE ChannelID == {destination_channel.id} LIMIT 1")

				role_to_add = ctx.guild.get_role(cs.fetchone()[0])


				await ctx.author.remove_roles(role_to_remove)
				await ctx.author.add_roles(role_to_add)

	# Set a channel for entry point. Otherwise the first role will have to be manually given.
	@commands.command(name="set_start_point", aliases=["set_entry_point", "setsp", "setep"], help="Set the starting point for server Map.")
	@commands.has_permissions(administrator=True)
	async def set_start_point(self, ctx, *, channel):
		channel_id = self.is_channel(channel)

		if (channel_id):
			cs.execute(f"UPDATE GuildData SET EntryChannel = {channel_id} WHERE GuildID == {ctx.guild.id} LIMIT 1")
			conn.commit()
			await ctx.send(f"Set entry point to {channel}. To grant role to players, use `!start` or `!enter`")
			# Check if the entry point has an associated role in Maps
			cs.execute(f"SELECT RoleID from Maps WHERE ChannelID == {channel_id} LIMIT 1")
			role_id_exists = cs.fetchone() is not None

			if (not role_id_exists):
				channel_obj = self.bot.get_channel(channel_id)
				channel_name = channel_obj.name
				new_role = await ctx.guild.create_role(name=channel_name)

				# Set channel perms for role
				await channel_obj.set_permissions(new_role, read_messages=True, send_messages=True, read_message_history=True)

				# Entry
				cs.execute(f"INSERT INTO Maps (GuildID, ChannelID, RoleID) VALUES ({ctx.guild.id}, {channel_id}, {new_role.id})")
				conn.commit()

				await ctx.send(f"Set up role for {channel}, use `!ac #{channel_obj.name}` to add connections.")

		else:
			await ctx("That is not a valid channel!")
			cont = False

	# Grant starting role
	@commands.command(name="start", aliases=["enter"], help="Grant players with the starting role of server Map. A player is anyone with a character set up from !nc")
	@commands.has_permissions(administrator=True)
	async def start(self, ctx):

		cont = True

		# Get Role
		cs.execute(f"SELECT EntryChannel FROM GuildData WHERE GuildID == {ctx.guild.id} LIMIT 1")
		entry_channel_id = cs.fetchone()[0]

		if (entry_channel_id == None):
			await ctx.send("You have not set an entry point or the server's map! Use `!setsp <channel_tag>` to do so.")
			cont = False

		if (cont):
			# Get user IDs
			cs.execute(f"SELECT UserID FROM UserData WHERE GuildID == {ctx.guild.id} AND PlayingAs NOT NULL")
			user_ids = cs.fetchall();

			# Get RoleID for Entry channel
			cs.execute(f"SELECT RoleID FROM Maps WHERE ChannelID == {entry_channel_id} LIMIT 1")
			entry_role_id = cs.fetchone()[0]

			msg = ''
			for user_id in user_ids:
				user = ctx.guild.get_member(user_id[0])

				entry_role = ctx.guild.get_role(entry_role_id)
				if (user != None):
					await user.add_roles(entry_role)
					msg += f"{user.name}, "

			# Completion notice
			await ctx.send(f"Assigned {entry_role} role to {msg[0:-2]}."[0:1500])

def setup(bot):
	bot.add_cog(Maps(bot))
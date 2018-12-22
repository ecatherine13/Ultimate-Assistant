import discord
from discord.ext import commands
from .config import *
import re
import datetime
import asyncio

class Announcements:
	def __init__(self, bot):
		self.bot = bot

	# Add a regular command to post in a channel. Requires a channelID, message, start time, and a frequency given as n hours.
	@commands.command(name="new_announcement", aliases=["na", "newannouncement"], help="Set up a new announcement. Requires a time and posting frequency in hours. Announcements can only be set on half-hour intervals.")
	@commands.has_permissions(administrator=True)
	async def new_announcement(self, ctx, *, channel):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		# To avoid tons of nested try staatements, use a continue value
		cont = True

		# First make sure they have enough slots. For now, I'm allowing up to 25 automated messages per guild. Because it's the embed field limit.
		cs.execute(f"SELECT * FROM Announcements WHERE GuildID == {ctx.guild.id}")
		announcements = cs.fetchall()

		if (len(announcements) >= 25):
			await ctx.send("You have reached the maximum number of announcements! (25)")
			cont = False

		# Make sure it's a proper channel
		# obtains int channel_id
		if(cont):
			# Capture channel id. TODO - account for old/new channels with <> 18 digits
			regex = "<#([0-9]{18})>"
			channel_id_str = re.findall(regex, channel)

			try:
				channel_id = int(channel_id_str[0])

			except:
				await ctx.send("That is not a proper channel! Please use `#channel-name` with the tag.")
				cont = False
		
		# Get the message.
		# Obtains str message
		if (cont):
			await ctx.send(f"Setting up message to post in {channel}. \nEnter message:")

			try:
				message = await self.bot.wait_for('message', check=pred, timeout=60)
				message = message.content
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again")
				cont = False

			# Message must be within Discord limits
			if (cont and len(message) > 2000):
				await ctx.send(f"That message is {str(len(message) - 2000)} characters too long! Please try again.")
				cont = False

		# Next, get a start date. It must be today or later.
		# Obtains datetime start_date, int guild_timezone_offset, datetime time_server
		if (cont):
			# Get server timezone
			cs.execute(f"SELECT * FROM GuildData WHERE GuildID == {ctx.guild.id}")

			guild_entry = cs.fetchone()
			guild_timezone_offset = guild_entry[4]

			# Set a start time and date, shift by guild time
			time_utc = datetime.datetime.utcnow()
			time_server = time_utc + datetime.timedelta(hours=guild_timezone_offset)

			# Set the start date.
			await ctx.send(time_server.strftime("It is currently **%Y-%m-%d, %H:%M** in the server timezone. \nEnter the date you would like this message to begin. (yyyy-mm-dd)"))
			try:
				start_date = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

		if (cont):
			date_match = re.search(r'^([0-9]{4})-([0-9]{2})-([0-9]{2})$', start_date.content)

			# Check input (date)
			try:
				year = date_match.group(1)
				month = date_match.group(2)
				day = date_match.group(3)

				# Guarantees no one accidentally pulls a Self Deprecation Day
				start_date = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)

				# Make sure it's in the future
				if (start_date < time_server):
					await ctx.send("You must enter today's date or later!")
					cont = False

			except:
				await ctx.send("That is not a valid date!")
				cont = False

		# If that's good, get the start time. If it's today, it must be later.
		# Obtains datetime start_time (includes the date from earlier.)
		if (cont):
			# Set the start time.
			await ctx.send(time_server.strftime("Enter a start time in 24-hr format. Only times on the half hour (00, 30) will be accepted. (hh:mm)"))

			try:
				start_time = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

		if (cont):
			time_match = re.search(r'^([0-9]{2}):(00|30)$', start_time.content)

			# Check input (time)
			try:
				hour = time_match.group(1)
				minute = time_match.group(2)

				# Make sure it's valid.
				start_time = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))

				# Make sure it's in the future
				if (start_time < time_server):
					await ctx.send("You must enter a time later than now!")
					cont = False

			except:
				await ctx.send("That is not a valid time! Only use half hour intervals (ex. 08:30, 14:00)")
				cont = False

		# Set an interval for repeat
		# Obtains int interval
		if (cont):
			await ctx.send("Set an interval (hours):")

			try:
				interval = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

		if (cont):
			interval_match = re.search(r'^([0-9]*)$', interval.content)

			# Check input (time)
			try:
				interval = interval_match.group(1)

			except:
				await ctx.send("That is not a valid number!")
				cont = False

		# Confirmation
		if (cont):
			# Summary
			embed = discord.Embed(title="Message Summary", description=message)
			embed.add_field(name="Channel", value=channel)
			embed.add_field(name="Start time", value=start_time.strftime("%Y-%m-%d, %H:%M"))
			embed.add_field(name="Posting Interval", value=f"Every {str(interval)} hrs")	
			await ctx.send(embed=embed)

			# Ask for confirmation
			await ctx.send("Are you happy with this? (y/n)")

			try:
				confirm = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

		if (cont):
			if (confirm.content.lower() == 'y' or confirm.content.lower() == "yes"):
				
				# Convert datetime start_time to utc using guild_timezone_offset, and to an integer
				start_time_utc = start_time - datetime.timedelta(hours=guild_timezone_offset)

				start_time_entry = int(start_time_utc.strftime("%Y%m%d%H%M"))

				# Set up
				cs.execute(f"INSERT INTO Announcements (GuildID, ChannelID, Message, Frequency, NextPosting) VALUES ({ctx.guild.id}, {channel_id}, ?, {interval}, {start_time_entry})", (f"{message}",))
				conn.commit()

				await ctx.send("Set! Use `!la | list_announcements | queue` to see all your announcements.")
			
			else:
				await ctx.send("Not confirmed. Finishing.")

	# Delete an announcement(s):
	@commands.command(name="del_announcement", aliases=["da", "deleteannouncement", "removeannouncement"], help="Remove one or more automated announcements.")
	@commands.has_permissions(administrator=True)
	async def del_announcement(self, ctx):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		guild_id = ctx.guild.id
		
		# Get announcements
		cs.execute(f"SELECT * FROM Announcements WHERE GuildID == {guild_id}")
		announcements = cs.fetchall()

		# Sort by time. Won't throw an arror if no announcements are there
		announcements.sort(key=lambda tup: tup[4])

		# Get Guild timezone shift
		cs.execute(f"SELECT Timezone FROM GuildData WHERE GuildID == {guild_id}")
		guild_tz_shift = cs.fetchone()[0]

		# Make embed
		if (guild_tz_shift < 0):
			embed = discord.Embed(title=f"Announcements for {ctx.guild}! (UTC{guild_tz_shift})")
		else:
			embed = discord.Embed(title=f"Announcements for {ctx.guild}! (UTC+{guild_tz_shift})")

		idx = 0 # User will input a number corresponding to announcement to delete
		for announcement in announcements:
			message = announcement[2]

			time = datetime.datetime.strptime(str(announcement[4]), '%Y%m%d%H%M') + datetime.timedelta(hours=guild_tz_shift)

			time_str = datetime.datetime.strftime(time, '%Y-%m-%d, %H:%M')

			interval = f"Every {announcement[3]} hours"
			channel = discord.utils.find(lambda c: c.id == announcement[1], ctx.guild.text_channels)

			if (len(message) > 50):
				embed.add_field(name=f"**[{idx}]** {message[0:50]}...", value=f" In #{channel} - {interval} \nNext post: {time_str}", inline=False)
			else:
				embed.add_field(name=f"**[{idx}]** {message[0:50]}", value=f" In #{channel} - {interval} \nNext post: {time_str}", inline=False)

			idx += 1
		
		embed.add_field(name=f"**[{idx}]** Exit", value="Exits/Cancels this command.")
		embed.set_footer(text="Timeout for response: 60 s")
		await ctx.send(embed=embed)

		# Get and check user input
		await ctx.send("Enter a number, or a list of comma separated numbers: (ex. 1, 3, 10)")

		try:
			entry = await self.bot.wait_for('message', check=pred, timeout=60)
			entry = entry.content
			idx_to_delete_strs = entry.split(',')
		except asyncio.TimeoutError:
			await ctx.send("Timer expired! Please try again.")
			idx_to_delete_strs = []

		for idx_str in idx_to_delete_strs:

			cont = True

			# Exit if int(idx_str)==idx
			if (int(idx_str) == idx):
				await ctx.send("Exiting!")
				cont = False
				break

			# Typecast to int will fail if it's not a number
			try:
				idx_to_delete = int(idx_str)

				# If that works, warn about numbers not in range (up to idx because exit option)
				if (0 > idx_to_delete or idx < idx_to_delete):
					await ctx.send(f"{idx_to_delete} is not within the given range!")
					cont = False

			except:
				await ctx.send(f"{idx_str} is not a valid number!")
				cont = False

			# If those both check out, delete
			if (cont):
				announcement_to_delete = announcements[idx_to_delete]

				cs.execute(f"DELETE FROM Announcements WHERE GuildID == {announcement_to_delete[0]} AND ChannelID == {announcement_to_delete[1]} AND Message == ? AND Frequency == {announcement_to_delete[3]} AND NextPosting == {announcement_to_delete[4]}", (f"{announcement_to_delete[2]}",))
				conn.commit()

				await ctx.send(f"Message {idx_to_delete} deleted!")

	# See announcement queue
	@commands.command(name="list_announcements", aliases=["la", "queue"], help="See upcoming announcements.")
	@commands.has_permissions(administrator=True)
	async def list_announcements(self, ctx):
		guild_id = ctx.guild.id
		
		# Get announcements
		cs.execute(f"SELECT * FROM Announcements WHERE GuildID == {guild_id}")
		announcements = cs.fetchall()

		cont = True

		# Sort by time. Won't throw an arror if no announcements are there
		announcements.sort(key=lambda tup: tup[4])

		# Get Guild timezone shift
		cs.execute(f"SELECT Timezone FROM GuildData WHERE GuildID == {guild_id}")
		guild_tz_shift = cs.fetchone()[0]

		# Make embed
		if (guild_tz_shift < 0):
			embed = discord.Embed(title=f"Announcements for {ctx.guild}! (UTC{guild_tz_shift})")
		else:
			embed = discord.Embed(title=f"Announcements for {ctx.guild}! (UTC+{guild_tz_shift})")
		for announcement in announcements:
			message = announcement[2]

			time = datetime.datetime.strptime(str(announcement[4]), '%Y%m%d%H%M') + datetime.timedelta(hours=guild_tz_shift)

			time_str = datetime.datetime.strftime(time, '%Y-%m-%d, %H:%M')

			interval = f"Every {announcement[3]} hours"
			channel = discord.utils.find(lambda c: c.id == announcement[1], ctx.guild.text_channels)

			if (len(message) > 50):
				embed.add_field(name=f"{message[0:50]}...", value=f" In #{channel} - {interval} \nNext post: {time_str}", inline=False)
			else:
				embed.add_field(name=f"{message[0:50]}", value=f" In #{channel} - {interval} \nNext post: {time_str}", inline=False)

		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(Announcements(bot))
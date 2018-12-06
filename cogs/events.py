import discord
from discord.ext import commands
from .config import *
import asyncio
import datetime

class Events:

	def __init__(self, bot):
		self.bot = bot

	async def on_ready(self):
		print(f"\nLogged in as {self.bot.user.name} - {self.bot.user.id}\nVersion: {discord.__version__}\n")
		await self.bot.change_presence(activity=discord.Game(name='$help'))

		# Correct announcements that have passed without posting (post times during bot downtime)
		time_now = datetime.datetime.utcnow()
		int_timestamp_now = int(time_now.strftime("%Y%m%d%H%M"))

		cs.execute(f"SELECT Frequency, NextPosting, GuildID, ChannelID FROM Announcements WHERE NextPosting < {int_timestamp_now}")
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

		self.bot.loop.create_task(self.announcement_task())

	async def on_guild_join(self, ctx):
		guild_id = ctx.id

		# If guild not in DB, add to it
		cs.execute(f"SELECT 1 FROM GuildData WHERE GuildID == {guild_id} LIMIT 1")
		guild_in_db = cs.fetchone() is not None
		
		if(guild_in_db == False):
			cs.execute(f"INSERT INTO GuildData (GuildID) VALUES ({guild_id})")
			conn.commit()

	async def on_member_join(self, ctx): # ctx is the Member
		guild_id = ctx.guild.id

		# Assign autorole if one is set up
		role_cs = cs.execute(f"SELECT AutoRole FROM GuildData WHERE GuildID={ctx.guild.id} LIMIT 1")
		
		role_id = role_cs.fetchone()[0]

		if(role_id != None):
			role = discord.utils.get(ctx.guild.roles, id=role_id)
			await ctx.add_roles(role)

	async def on_member_remove(self, ctx):
		# TODO - Remove from User table?
		return 0

	async def on_guild_remove(self, ctx):
		# TODO - Remove guild data from all tables
		return 0

	# Announcement background task
	# TODO Allow for time pauses
	async def announcement_task(self):
		in_sync = False # Changes to true on the first half hour available
		while (True):
			time_now = datetime.datetime.utcnow()

			if (not in_sync):
				if(time_now.minute == 0 or time_now.minute == 30):
					in_sync = True
				else:
					await asyncio.sleep(15) # Check every 15 seconds

			if (in_sync):
				time_now_int = int(time_now.strftime("%Y%m%d%H%M"))
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
					channel = self.bot.get_channel(channel_id)
					await channel.send(message)

					# Update next posting
					current_posting_datetime = datetime.datetime.strptime(str(current_posting), "%Y%m%d%H%M")	
					next_posting = current_posting_datetime + datetime.timedelta(hours=frequency)
					next_posting = int(next_posting.strftime("%Y%m%d%H%M"))

					# Update entry
					cs.execute(f"UPDATE Announcements SET NextPosting = {next_posting} WHERE GuildID == {guild_id} AND ChannelID == {channel_id} AND Message = ?", (message,))
					conn.commit()

				await asyncio.sleep(1800) # 30 minutes

def setup(bot):
	bot.add_cog(Events(bot))
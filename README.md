# Ultimate Assistant

This is a Discord bot built with the purpose of catering to a community that gathers around the visual novel, *Danganronpa: Trigger Happy Havoc* and its sequels. The community focuses on writing original characters, crafting mysteries to solve together, and building imaginative settings to host roleplaying games. This project aims to lessen the workload on game hosts and offer utilities for both players and hosts.

This bot is still in 'beta', and errors are automatically DMed to the developer. The report contains the server ID, channel ID, user ID, attempted command, and the error thrown. This info is all readily available to any bot and *cannot* be used to identify your private information. The developer also welcomes your feedback and suggestions, which can be given semi-anonymously with:

`!feedback Your message here`

UA will DM the developer with the message. User ID is provided in order to screen for misuse/harassment.

To view this README, use:

`!source | !docs | !readme`

## Important

This bot functions on the premise that admin will set up each player with a character. Multiple characters can be assigned to one user, but only the most recently initiated one will be considered (TODO: switching command). Upon initiation, the character is assigned a unique nickname for look-up purposes. This is to accomodate repeated names, and so that long names do not need to be fully typed. In most cases, the nickname will just be the character's first name.

To use every feature of UA, the bot's highest role will need the following permissions: (TODO: Better handling of BotMissingPermissions error)

```
Manage Roles
Manage Channels
Read Text Channels
Send Messages
Manage Messages
Read Message History
Embed Links
Attach Files
```

## Contents

[General](#general)

[Player](#player)
* [Utilities](#player_utilities)
* [Inventory / Gacha](#player_inventory)
* [Moving / Investigation](#player_moving)

[Admin](#admin)
* [Profile Setup](#admin_setup)
* [Utilities](#admin_utilities)
* [Automated Announcements](#auto_announce)
* [Inventory / Gacha](#admin_inventory)
* [Maps](#admin_moving)
* [Investigation](#admin_investigate)

[Self-hosting](#hosting)

[Future Updates](#future_updates)

## General <a name="general"></a>

Command | Aliases | Example | Description
--- | --- | --- | ---
!roll \<dice\>| r | !roll 2d12-d20+3 | Uses standard d20 notation
!lookup \<name\> | search, handbook, profile | !lookup jane | See public information on any character that has been set up
!nicknames | lcn, names, list_char_nicknames, listnames, listnicknames | - | See a list of nicknames for server. 

## Player <a name="player"></a>

### Utilities <a name="player_utilities"></a>

Command | Aliases | Example | Description
--- | --- | --- | ---
!playing_as | iam, my_char, mc | - | Displays the name of your in-game character as set up by an administrator. 
!anon_dm \<character\> \<message\>| anondm, anon_pm, anonpm, adm, apm | !adm Sonia A secret message for you | Send an anonymous DM to a player. This feature is *OFF* by default and must be enabled by an administrator with `!toggle_adm`. ***Disclaimer: The server admins are automatically DMed a record of the message. The developer is not responsible for abuse of this feature.***

### Inventory / Gacha <a name="player_inventory"></a>

Fairly straighforward inventories. They are currently **case sensitive** and do not allow exact repeats of names.

Command | Aliases | Example | Description
--- | --- | --- | ---
!inventory | items | - | Displays your inventory. 
!take \<item name\> \[description\]| - |!take book A red book from the library| Adds an item to your inventory. Remember to use quotation marks if "item name" is more than one word long. Description is optional.
!drop \<item name\> | - | !drop book | Removes an item from your inventory.
!gacha | gatcha, draw, g | - | Draws from the server gacha if one is set up. Adds new items to inventory automatically and notifies of repeats.
!money | wallet, coins, currency | - | Shows how much currency you have. You'll need at least 1 to draw from gacha. 

### Moving / Investigation <a name="player_moving"></a>

`!go` is used in situations where certain areas are meant to stay separated from one another. Admin can set up connections, and UA will create roles associated with specified channels. Players will only be allowed to move to areas connected to one associated with a role they already have. TLDR: self assigned roles that are set up to give view/write permissions to specified channels

**Requires Role Management Permissions**

Investigations / checks allow players to interact with the environment without needing a host present. Hosts are responsible for making investigatable objects clear. `!investigate` must be used in the appropriate channel. Remote investigations can be performed in secret with `!rinvestigate`, and must specify a channel to search.

Command | Aliases | Example | Description
--- | --- | --- | ---
!go \<channel-name\>| goto, move, moveto | !go main-hall | Assigns the appropriate role for destination if it's been set up and the user has a correct role.
!investigate \<object\> | check | !investigate locked box | On success, DMs the user investigation results, or notifies them of failure.
!rinvestigate \<channel\> \<object\> | rcheck, remote_investigate, remoteinvestigate | !rcheck #lobby blue curtains | Requires the channel tag, otherwise functions exactly like regular `!investigate`.

## Admin <a name="admin"></a>

### Profile Setup <a name="admin_setup"></a>

As mentioned above, each player must be assigned a character in order to use the inventory, gacha, investigation, and movement features. The setup commands enforce that no nicknames are repeated within a server.

Command | Aliases | Example | Description
--- | --- | --- | ---
!new_char \<player\> \<full name\> | newchar, nc | !nc @Serenity Jane Doe | Assigns a character to the pinged player. If you don't want to ping the user, this can be done in private. You will be prompted to input a unique nickname.
!update_char \<nickname\> | updatechar, uc | !uc jane | Add public information via a selection menu.
!rem_char_info \<nickname\> | ucr, uc_remove | !ucr jane | Remove a piece of information from a public profile.
!rem_char \<nickname\> | rc, remchar | !rc john | *Permanently* removes character from the server, wiping inventory, public information, and currency. Prompts with a confirmation message first.

### Utilities <a name="admin_utilities"></a>

Command | Aliases | Example | Description
--- | --- | --- | ---
!set_autorole \[role\] | sar, set_ar, setar, ar | !ar, !ar @Undecided | Leave blank to respond to a list. Otherwise, be sure to tag the role. New members who join the server will be given that role. Can only assign roles below the bot's highest role.
!toggle_adm | - | - | Toggles Anonymous DMs. By default the feature is OFF.

### Automated Announcements <a name="auto_announce"></a>

To automate an announcement, first set your server timezone with `!tz`. By default, this is set to UTC+0. Announcements can be made on any half hour interval, and can be repeated in intervals of *n* hours. 

**Requires Message Sending Permissions for announcement channel**

Command | Aliases | Example | Description
--- | --- | --- | ---
!set_timezone \[UTC Offset\]| tz, timezone, settimezone | !tz, !tz +1 | If left blank, prompts the user to input an integer corresponding to UTC offset. (TODO: Allow half hour timezones)
!list_announcements | la, queue | - | Shows each announcement set up for a server and their next posting times.
!new_announcement \<\#channe-namel\> | na, newannouncement | !na #time-announcements |Requires a channel tag to specifiy where the announcement will send. Guides user through setup of message content and repetition interval.
!del_announcement | da, deletennouncement, removeannouncement | - | Remove one or more announcement using a comma separated list.

### Inventory / Gacha <a name="admin_inventory"></a>

Hosts may give or take items to/from any player. This does not notify the player. Along with that, the following commands are used to set up a gacha that can be drawn by any player. Each gacha item requires a unique name and a description. Images are optional. Gachas require at least 1 unit of currency, which is granted to players by the host.

Command | Aliases | Example | Description
--- | --- | --- | ---
!ainventory \<nickname\> | aitems | !aitems sakura | Displays any character's inventory.
!give \<nickname\> | give_item | !give leon | Prompts for an item name and description. 
!confiscate \<nickname\> | take_from, takefrom | !takefrom naomi | Displays inventory and prompts for an item name (case sensitive).
!set_currency \<name\> | - | !set_currency Yen | Allows renaming the server's currency. Defaults to 'Coins' if not set.
!amoney \<nickname\> | awallet | !amoney anne | View how much currency a player has.
!give_money \<amount\>| pay, givemoney, givecoins, give_coins | !pay anne | Grants the player currency. Enter a negative number to take currency.
!gacha_list | gachalist, gatcha_list, gatchalist | - | Lists gacha items for server with descriptions.
!new_item \<item name\> | ni, newitem | !ni Another Battle | Adds an item to the server gacha. Prompts for a description and an optional image.
!rem_items | ri, remitem | - | Displays a menu to remove one or more items from the gacha.


### Maps <a name="admin_moving"></a>

These commands can be used in situtions where you would like to assign roles to certain channels or areas that should only be seen by those playing in them. A map is formed when one or more connections are defined between two channels. It is also recommended to make a 'starting channel' as an entry point for the map, as the `!go` command checks existing roles. 

To set up a map, first use `!new_area_role #channel-name` to add a channel to the map. Define outgoing connections from it using `!set_connections #channel-name`. The entry point can be specified with `!set_start_point #channel-name`, and `!start` grants that role to all users with a character set up.

ex. `#elevator-f1` connects to `#elevator-f2`. To hide floor 1 from those in floor 2 and vice versa:

1. `!nar #elevator-f1` (bot creates `elevator-f1` role, prompts step 2)
2. `!sc #elevator-f1` -> `#elevator-f2` -> two-way connection (bot creates `elevator-f2` role if needed) 

The `elevator` channels will automatically have the roles added to them with read, write, and history permissions. To hide all of floor 1, assign the `elevator-f1` role to all channels, repeat for floor 2. If floor 1 is the starting point, it is recommended to run:

3. `!setsp #elevator-f1` (bot assigns all players the `elevator-f1` role)
4. `!start`

Command | Aliases | Example | Description
--- | --- | --- | ---
!map | connections, view_connections | - | See a list of channels and their outgoing connections.
!new_area_role \<\#channel-name\> | nar, newarearole | !nar #main-hall | Tag a channel to add it as a point on the map.
!set_connections \<\#channel-name\> | sc, map_connections, mapconnections | !sc #main-hall | Tag one or more *outgoing* channels, separated with a comma. Will prompt an option for a two-way connection and create roles as needed.
!set_start_point \<\#channel-name\> | setsp, set_entry_point, setep | !setsp #main-hall | Defines an entry point for the map.
!start | enter | - | Assigns the role defined with `!set_start_point` to all users with a character set up.

### Investigation <a name="admin_investigate"></a>

Set up objects in existing channels that players can check out for cool information. The information is sent in DMs for secrecy. Be sure to add several names for the object so that players don't get too frustrated trying to guess the exact name. ex. `curtain, curtains, blue curtains`

Command | Aliases | Example | Description
--- | --- | --- | ---
!investigations | - | - | See a list of all objects set up, ordered by channel.
!new_investigation \<\#channel-name\> | ninv, newinvestigation | !ninv #hallway-1 | Set up a new object in tagged channel. User will be prompted to input a list of names and the info that will be DMed on successful investigation.
!rem_investigation | rinv, reminvestigation | - | Displays a menu to select objects to remove.

## Self-Hosting <a name="hosting"></a>

UA isn't meant to be self-hosted yet, but it can be done. UA was developed on Ubuntu 16.04 with Python 3.6 and discord.py rewrite version.

1. Obtain a bot token by following the instructions here: 

https://discordpy.readthedocs.io/en/rewrite/discord.html

2. Clone the repository:

`git clone https://github.com/ecatherine13/Ultimate-Assistant.git`

3. Create a file called `token.txt`, and paste your bot token as a single line.

4. This bot currently sends error reports to the developer's Discord account. To disable this, comment out the appropriate line in `main.py`. Otherwise, create a file called `owner_id.txt`, and paste your 18 digit user id as a single line.

5. Change `master-empty.db` to `master.db`

6. It's highly recommended to use a python3.6 virtual environment. To do so, follow the instructions here:

https://docs.python.org/3.6/library/venv.html

7. Activate the virtual environment:

`source </path/to/venv>bin/activate`

8. Install discord.py rewrite. One way to do this is with:

`pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py`

UA does not need voice features, but if desired, you may use:

`pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py[voice]`

9. Run the bot with:

`python main.py`

## Future Updates <a name="future_updates"></a>

* Better error handling
* Performance improvements
* Channel archiving
* Fun things
"""
Discord Execution Tools for EXILES AI
Defines tool schemas for Gemini Function Calling and async execution functions.
"""

import discord
import logging

logger = logging.getLogger("ExilesTools")

DISCORD_TOOLS_SCHEMA = [
    {
        "function_declarations": [
            {
                "name": "rename_server",
                "description": "Renames the Discord server/guild to a new name.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "new_name": {"type": "STRING", "description": "The exact new name for the server."}
                    },
                    "required": ["new_name"]
                }
            },
            {
                "name": "create_channel",
                "description": "Creates a new text or voice channel in the Discord server.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING", "description": "Name of the channel to create."},
                        "channel_type": {"type": "STRING", "description": "Type of channel: 'text' or 'voice'. Defaults to 'text'."},
                        "category_name": {"type": "STRING", "description": "Optional category name to place the channel inside."}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "delete_channel",
                "description": "Deletes a channel from the Discord server by its name.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "channel_name": {"type": "STRING", "description": "Name of the channel to delete."}
                    },
                    "required": ["channel_name"]
                }
            },
            {
                "name": "lock_channel",
                "description": "Locks a text channel so @everyone cannot send messages in it.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "channel_name": {"type": "STRING", "description": "Name of the channel to lock."}
                    },
                    "required": ["channel_name"]
                }
            },
            {
                "name": "unlock_channel",
                "description": "Unlocks a locked channel so @everyone can chat again.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "channel_name": {"type": "STRING", "description": "Name of the channel to unlock."}
                    },
                    "required": ["channel_name"]
                }
            },
            {
                "name": "assign_role",
                "description": "Assigns a role to a server member by username or display name.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "member_name": {"type": "STRING", "description": "Username or nickname of the member."},
                        "role_name": {"type": "STRING", "description": "Name of the role to assign."}
                    },
                    "required": ["member_name", "role_name"]
                }
            },
            {
                "name": "remove_role",
                "description": "Removes a role from a server member.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "member_name": {"type": "STRING", "description": "Username or nickname of the member."},
                        "role_name": {"type": "STRING", "description": "Name of the role to remove."}
                    },
                    "required": ["member_name", "role_name"]
                }
            },
            {
                "name": "send_embed",
                "description": "Sends a clean Crimson Red Discord Embed to any channel in the server.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "channel_name": {"type": "STRING", "description": "Name of the target channel (e.g. 'announcements', 'general', 'scrim-briefing')."},
                        "title": {"type": "STRING", "description": "Title of the embed."},
                        "description": {"type": "STRING", "description": "Description/content of the embed."},
                        "ping_everyone": {"type": "BOOLEAN", "description": "Whether to include an @everyone ping with the embed."}
                    },
                    "required": ["channel_name", "title", "description"]
                }
            },
            {
                "name": "set_slowmode",
                "description": "Sets the slowmode cooldown delay in seconds on a text channel.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "channel_name": {"type": "STRING", "description": "Name of the channel."},
                        "seconds": {"type": "INTEGER", "description": "Slowmode delay in seconds (0 to disable)."}
                    },
                    "required": ["channel_name", "seconds"]
                }
            },
            {
                "name": "purge_messages",
                "description": "Deletes recent messages in a specified channel.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "channel_name": {"type": "STRING", "description": "Name of the channel to clean."},
                        "count": {"type": "INTEGER", "description": "Number of messages to delete (default 10)."}
                    },
                    "required": ["channel_name"]
                }
            }
        ]
    }
]


async def execute_tool(bot: discord.Client, guild: discord.Guild, func_name: str, args: dict) -> dict:
    """Executes the tool requested by Gemini against Discord API."""
    logger.info(f"Executing tool '{func_name}' with args: {args}")

    try:
        if func_name == "rename_server":
            new_name = args.get("new_name", "").strip()
            if not new_name:
                return {"status": "error", "message": "No new name provided."}
            await guild.edit(name=new_name)
            return {"status": "success", "result": f"Server name successfully changed to '{new_name}'"}

        elif func_name == "create_channel":
            name = args.get("name", "").strip().lower().replace(" ", "-")
            ctype = args.get("channel_type", "text").lower()
            category_name = args.get("category_name", "").strip().lower()

            category = None
            if category_name:
                category = discord.utils.find(lambda c: category_name in c.name.lower(), guild.categories)

            if ctype == "voice":
                ch = await guild.create_voice_channel(name=name, category=category)
            else:
                ch = await guild.create_text_channel(name=name, category=category)
            return {"status": "success", "result": f"Channel #{ch.name} (ID: {ch.id}) created successfully."}

        elif func_name == "delete_channel":
            target_name = args.get("channel_name", "").strip().lower().replace("#", "")
            ch = discord.utils.find(lambda c: target_name in c.name.lower(), guild.channels)
            if not ch:
                return {"status": "error", "message": f"Channel '{target_name}' not found."}
            name = ch.name
            await ch.delete()
            return {"status": "success", "result": f"Channel #{name} has been deleted."}

        elif func_name == "lock_channel":
            target_name = args.get("channel_name", "").strip().lower().replace("#", "")
            ch = discord.utils.find(lambda c: target_name in c.name.lower() and isinstance(c, discord.TextChannel), guild.text_channels)
            if not ch:
                return {"status": "error", "message": f"Text channel '{target_name}' not found."}
            everyone_role = guild.default_role
            await ch.set_permissions(everyone_role, send_messages=False)
            return {"status": "success", "result": f"Channel #{ch.name} has been locked for @everyone."}

        elif func_name == "unlock_channel":
            target_name = args.get("channel_name", "").strip().lower().replace("#", "")
            ch = discord.utils.find(lambda c: target_name in c.name.lower() and isinstance(c, discord.TextChannel), guild.text_channels)
            if not ch:
                return {"status": "error", "message": f"Text channel '{target_name}' not found."}
            everyone_role = guild.default_role
            await ch.set_permissions(everyone_role, send_messages=True)
            return {"status": "success", "result": f"Channel #{ch.name} has been unlocked for @everyone."}

        elif func_name == "assign_role":
            member_name = args.get("member_name", "").strip().lower()
            role_name = args.get("role_name", "").strip().lower()

            member = discord.utils.find(lambda m: member_name in m.name.lower() or (m.nick and member_name in m.nick.lower()), guild.members)
            role = discord.utils.find(lambda r: role_name in r.name.lower(), guild.roles)

            if not member:
                return {"status": "error", "message": f"Member '{member_name}' not found."}
            if not role:
                return {"status": "error", "message": f"Role '{role_name}' not found."}

            await member.add_roles(role)
            return {"status": "success", "result": f"Role '@{role.name}' assigned to {member.name}."}

        elif func_name == "remove_role":
            member_name = args.get("member_name", "").strip().lower()
            role_name = args.get("role_name", "").strip().lower()

            member = discord.utils.find(lambda m: member_name in m.name.lower() or (m.nick and member_name in m.nick.lower()), guild.members)
            role = discord.utils.find(lambda r: role_name in r.name.lower(), guild.roles)

            if not member:
                return {"status": "error", "message": f"Member '{member_name}' not found."}
            if not role:
                return {"status": "error", "message": f"Role '{role_name}' not found."}

            await member.remove_roles(role)
            return {"status": "success", "result": f"Role '@{role.name}' removed from {member.name}."}

        elif func_name == "send_embed":
            target_name = args.get("channel_name", "").strip().lower().replace("#", "")
            title = args.get("title", "")
            desc = args.get("description", "")
            ping = args.get("ping_everyone", False)

            ch = discord.utils.find(lambda c: target_name in c.name.lower() and isinstance(c, discord.TextChannel), guild.text_channels)
            if not ch:
                return {"status": "error", "message": f"Channel '{target_name}' not found."}

            embed = discord.Embed(title=title, description=desc, color=0xDC143C)
            content = "@everyone" if ping else None
            await ch.send(content=content, embed=embed)
            return {"status": "success", "result": f"Embed posted successfully in #{ch.name}."}

        elif func_name == "set_slowmode":
            target_name = args.get("channel_name", "").strip().lower().replace("#", "")
            seconds = int(args.get("seconds", 0))

            ch = discord.utils.find(lambda c: target_name in c.name.lower() and isinstance(c, discord.TextChannel), guild.text_channels)
            if not ch:
                return {"status": "error", "message": f"Channel '{target_name}' not found."}

            await ch.edit(slowmode_delay=seconds)
            return {"status": "success", "result": f"Slowmode on #{ch.name} set to {seconds} seconds."}

        elif func_name == "purge_messages":
            target_name = args.get("channel_name", "").strip().lower().replace("#", "")
            count = min(int(args.get("count", 10)), 50)

            ch = discord.utils.find(lambda c: target_name in c.name.lower() and isinstance(c, discord.TextChannel), guild.text_channels)
            if not ch:
                return {"status": "error", "message": f"Channel '{target_name}' not found."}

            deleted = await ch.purge(limit=count)
            return {"status": "success", "result": f"Purged {len(deleted)} messages from #{ch.name}."}

        else:
            return {"status": "error", "message": f"Unknown tool '{func_name}'"}

    except Exception as e:
        logger.error(f"Error executing tool {func_name}: {e}")
        return {"status": "error", "message": str(e)}

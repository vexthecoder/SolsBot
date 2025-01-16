import discord, json, threading, pyautogui, requests, os, keyboard, time # type: ignore

from discord.ext import commands # type: ignore
from discord import app_commands # type: ignore
from datetime import datetime

running_event = threading.Event()
running_event.set()

CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r") as file:
    config = json.load(file)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

def update_config(key, value):
    config[key] = value
    with open(CONFIG_PATH, "w") as file:
        json.dump(config, file, indent=4)

# setup bot and register commands
def setup_bot(running_event):
    @bot.event
    async def on_ready():
        print(f"Bot is online as {bot.user}")
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} commands with Discord.")
        except Exception as e:
            print(f"Discord Bot | Error syncing commands: {e}")
        if not config.get("DiscordBot_UserID"):
            print("Warning: No User ID configured. Commands will not be executable until a valid User ID is set.")
            webhook_url = config.get("WebhookLink")
            if webhook_url:
                embeds = [{
                    "title": "Warning",
                    "description": f"User ID Not Specified\nPlease specify your Discord User ID to run commands.",
                    "color": 7289397
                }]
            else:
                local_embed = discord.Embed(
                    title="Warning",
                    description="Webhook URL is not configured.\nPlease configure your webhook", 
                    color=discord.Color.from_rgb(128, 128, 128)
                )
                await ctx.send(embed=local_embed, ephemeral=True) # type: ignore

    @app_commands.command(name="screenshot", description="Take a screenshot of the current screen")
    async def screenshot(ctx: discord.Interaction):
        user_id = ctx.user.id

        if not config.get("DiscordBot_UserID"):
            local_embed = discord.Embed(
                title="Warning",
                description="No User ID is configured. Please set your User ID in the bot settings to use commands.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return

        if str(user_id) != str(config.get("DiscordBot_UserID")):
            local_embed = discord.Embed(
                title="Warning",
                description="You do not have permission to use this command. Ensure the correct User ID is set.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return
        
        await ctx.response.defer(ephemeral=True)

        try:
            os.makedirs("images", exist_ok=True)

            screenshot_path = "images/current_screen.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)

            current_time = datetime.now().strftime("%H:%M:%S")
            webhook_url = config.get("WebhookLink")
            
            if webhook_url:
                embeds = [{
                    "title": "Screenshot Captured",
                    "description": f"Screenshot taken at {current_time}",
                    "color": 7289397,
                    "image": {"url": f"attachment://{os.path.basename(screenshot_path)}"}
                }]

                with open(screenshot_path, "rb") as image_file:
                    payload = {
                        "payload_json": json.dumps({
                            "embeds": embeds
                        })
                    }
                    files = {"file": (os.path.basename(screenshot_path), image_file, "image/png")}
                    webhook_response = requests.post(
                        webhook_url,
                        data=payload,
                        files=files
                    )

                if webhook_response.status_code in [200, 204]:
                    local_embed = discord.Embed(
                        description="Screenshot sent successfully.", 
                        color=discord.Color.from_rgb(128, 128, 128)
                    )
                    await ctx.followup.send(embed=local_embed, ephemeral=True)
                else:
                    local_embed = discord.Embed(
                        description=f"Failed to send screenshot. Status code: {webhook_response.status_code}", 
                        color=discord.Color.from_rgb(128, 128, 128)
                    )
                    await ctx.followup.send(embed=local_embed, ephemeral=True)
            else:
                local_embed = discord.Embed(
                    description="Webhook URL is not configured.", 
                    color=discord.Color.from_rgb(128, 128, 128)
                )
                await ctx.followup.send(embed=local_embed, ephemeral=True)
        except Exception as e:
            local_embed = discord.Embed(
                description=f"Discord Bot | /screenshot | Error taking screenshot: {e}", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)

    @app_commands.command(name="stop", description="Stop a macro.\nYou can change the keybind in the settings tab.")
    async def stop(ctx: discord.Interaction):
        user_id = ctx.user.id

        if not config.get("DiscordBot_UserID"):
            local_embed = discord.Embed(
                title="Warning",
                description="No User ID is configured. Please set your User ID in the bot settings to use commands.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return

        if str(user_id) != str(config.get("DiscordBot_UserID")):
            local_embed = discord.Embed(
                title="Warning",
                description="You do not have permission to use this command. Ensure the correct User ID is set.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return
        
        stop_key = config.get("macro_stop_key", "F3")
        keyboard.press_and_release(stop_key)
        local_embed = discord.Embed(
            description="Macro stopped.\nKey pressed: " + stop_key, 
            color=discord.Color.from_rgb(128, 128, 128)
        )
        await ctx.followup.send(embed=local_embed, ephemeral=True)

    @app_commands.command(name="pause", description="Pause a macro.\nYou can change the keybind in the settings tab.")
    async def pause(ctx: discord.Interaction):
        user_id = ctx.user.id

        if not config.get("DiscordBot_UserID"):
            local_embed = discord.Embed(
                title="Warning",
                description="No User ID is configured. Please set your User ID in the bot settings to use commands.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return

        if str(user_id) != str(config.get("DiscordBot_UserID")):
            local_embed = discord.Embed(
                title="Warning",
                description="You do not have permission to use this command. Ensure the correct User ID is set.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return
        
        pause_key = config.get("macro_pause_key", "F2")
        keyboard.press_and_release(pause_key)
        local_embed = discord.Embed(
            description="Macro paused.\nKey pressed: " + pause_key, 
            color=discord.Color.from_rgb(128, 128, 128)
        )
        await ctx.followup.send(embed=local_embed, ephemeral=True)

    @app_commands.command(name="start", description="Start a macro.\nYou can change the keybind in the settings tab.")
    async def start(ctx: discord.Interaction):
        user_id = ctx.user.id

        if not config.get("DiscordBot_UserID"):
            local_embed = discord.Embed(
                title="Warning",
                description="No User ID is configured. Please set your User ID in the bot settings to use commands.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return

        if str(user_id) != str(config.get("DiscordBot_UserID")):
            local_embed = discord.Embed(
                title="Warning",
                description="You do not have permission to use this command. Ensure the correct User ID is set.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return
        
        start_key = config.get("macro_start_key", "F1")
        keyboard.press_and_release(start_key)
        local_embed = discord.Embed(
            description="Macro started.\nKey pressed: " + start_key, 
            color=discord.Color.from_rgb(128, 128, 128)
        )
        await ctx.followup.send(embed=local_embed, ephemeral=True)

    @app_commands.command(name="ping", description="How laggy is your pc?")
    async def ping(ctx: discord.Interaction):
        latency = round(bot.latency * 1000)  # Convert to milliseconds
    
        if latency <= 100:
            color = discord.Color.green()
        elif 100 < latency < 300:
            color = discord.Color.yellow()
        else:
            color = discord.Color.red()
    
        local_embed = discord.Embed(
                title="Pong...",
                description=f"Latency: {latency}ms", 
                color=color
        )
        await ctx.response.send_message(embed=local_embed, ephemeral=True)

    @app_commands.command(name="chat", description="Send a message to the Roblox chat.\nDo NOT use this command while running a macro.")
    async def chat(ctx: discord.Interaction, message: str):
        user_id = ctx.user.id

        if not config.get("DiscordBot_UserID"):
            local_embed = discord.Embed(
                title="Warning",
                description="No User ID is configured. Please set your User ID in the bot settings to use commands.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return

        if str(user_id) != str(config.get("DiscordBot_UserID")):
            local_embed = discord.Embed(
                title="Warning",
                description="You do not have permission to use this command. Ensure the correct User ID is set.", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)
            return

        keyboard.press_and_release("/")
        time.sleep(1)
        keyboard.write(message)
        time.sleep(1)
        keyboard.press_and_release("enter")
        try:
            os.makedirs("images", exist_ok=True)

            screenshot_path = "images/chat.png"
            screenshot = pyautogui.screenshot(region=(0, 0, 600, 600))
            screenshot.save(screenshot_path)

            current_time = datetime.now().strftime("%H:%M:%S")
            webhook_url = config.get("WebhookLink")
            
            if webhook_url:
                embeds = [{
                    "title": "Message Sent",
                    "description": f"[{current_time}] Message Sent: '{message}'",
                    "color": 7289397,
                    "image": {"url": f"attachment://{os.path.basename(screenshot_path)}"}
                }]

                with open(screenshot_path, "rb") as image_file:
                    payload = {
                        "payload_json": json.dumps({
                            "embeds": embeds
                        })
                    }
                    files = {"file": (os.path.basename(screenshot_path), image_file, "image/png")}
                    webhook_response = requests.post(
                        webhook_url,
                        data=payload,
                        files=files
                    )

                if webhook_response.status_code in [200, 204]:
                    local_embed = discord.Embed(
                        description=f"Message sent: '{message}'", 
                        color=discord.Color.from_rgb(128, 128, 128)
                    )
                    await ctx.followup.send(embed=local_embed, ephemeral=True)
                else:
                    local_embed = discord.Embed(
                        description=f"Failed to send screenshot. Status code: {webhook_response.status_code}", 
                        color=discord.Color.from_rgb(128, 128, 128)
                    )
                    await ctx.followup.send(embed=local_embed, ephemeral=True)
            else:
                local_embed = discord.Embed(
                    description="Webhook URL is not configured.", 
                    color=discord.Color.from_rgb(128, 128, 128)
                )
                await ctx.followup.send(embed=local_embed, ephemeral=True)
        except Exception as e:
            local_embed = discord.Embed(
                description=f"Discord Bot | /chat | Error taking screenshot: {e}", 
                color=discord.Color.from_rgb(128, 128, 128)
            )
            await ctx.followup.send(embed=local_embed, ephemeral=True)

    # add commands to tree
    bot.tree.add_command(start)
    bot.tree.add_command(pause)
    bot.tree.add_command(stop)
    bot.tree.add_command(screenshot)
    bot.tree.add_command(chat)
    bot.tree.add_command(ping)

# start the bot
def start_bot(running_event):
    setup_bot(running_event)
    bot_token = config.get("DiscordBot_Token")
    bot.run(bot_token)
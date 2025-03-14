## Note
SolsBot will no longer be worked on. If you enjoyed SolsBot, feel free to check out some other Sol's RNG related projects I've contributed to:
- [Oyster Detector](https://github.com/vexthecoder/OysterDetector)
- [SolsCalc](https://github.com/ImPunken/SolsCalc)
- [Aurium](https://github.com/goldfish-cool/Goldens-Macro/)

# SolsBot
## JumpTo
[Installation Guide](https://github.com/vexthecoder/SolsBot?tab=readme-ov-file#Installation)<br>
[Features](https://github.com/vexthecoder/SolsBot?tab=readme-ov-file#Features)<br>
[FAQ](https://github.com/vexthecoder/SolsBot?tab=readme-ov-file#FAQ)<br>
[Setup](https://github.com/vexthecoder/SolsBot?tab=readme-ov-file#Setup)<br>
[Credits](https://github.com/vexthecoder/SolsBot?tab=readme-ov-file#Credits)<br>
[To-Do](https://github.com/vexthecoder/SolsBot?tab=readme-ov-file#To-Do)<br>

## Installation
  - Download the most recent version of SolsBot through the most recent [GitHub Release](https://github.com/vexthecoder/SolsBot/releases/latest) (Download source code ZIP)
  - After downloading, extract the ZIP file to your desired directory
  - Open the "setup" folder and run install.bat (this will open the requirement installer)
  - Choose option 4 and open every installer it downloads (besides Visual Studio Code).<br>
When installing python, make SURE to click "Add python.exe to PATH" in the bottom left of the python installer.
  - Once you have installed everything, open the install.bat file back up and choose option 6. This should install all the python requirements.
  - Once everything finishes installing, you should be good to go. Just open up start.bat in the main directory.

## Running SolsBot
  - You can run the application by opening "start.bat"

## Features
SolsBot has a couple of different features it is capable of which are mostly Discord related. These include:
- Discord Integration
  - Discord Webhook Support
  - Discord Bot Remote Commands
- Server Sniper
- External Macro Support
- More to come!..

## FAQ
(1) I have finished setting up the discord bot but the slash commands wont show up!<br>
--> Discord takes a while to sync up the commands, so the best bet you have is to keep refreshing your discord app or just wait a while.

(2) I set a User ID but it still says I don't have permission to use the commands!<br>
--> Make sure you have set the User ID to YOUR User ID and NOT the bot's User ID. Close and reopen the application to apply the changes.

(3) Do I have to have a webhook setup to use the Discord Bot features?<br>
--> At the current moment, yes, but I will be changing that later down the line so you wont have to set that up.

(4) Can I create multiple keywords?<br>
--> Yes! In the Server Sniper config editor, you can separate multiple keywords with a , (comma).

(5) What all do you plan on adding to SolsBot?<br>
--> Honestly, I'm not too sure, I feel like I have added everything I wanted. But!, if you have any suggestions on what to add, feel free to [DM me on Discord](https://discord.com/users/1018875765565177976) anytime!

(6) Whenever I run start.bat, it closes instantly. How do I fix this?<br>
--> This issue is usually caused by you not having the right version of Python, or you have not installed all of the Python requirements. You can fix this by going through the installation steps again. If the issue persists, try uninstalling and reinstalling Python version 3.12.7.

(7) The console keeps getting spammed with "Server Sniper | Error occurred: 0". How do I fix this?<br>
--> This issue is usually caused by an invalid Auth Key or Discord rate limiting you, but hardly the latter. You can fix this issue by going through the setup steps for the Server Sniper module again. Follow the steps VERY carefully.

(?) Soon...

## Setup
### Discord Bot
Follow [this tutorial](https://www.youtube.com/watch?v=-m-Z7Wav-fM) to create your discord bot and paste the token into the "Discord Bot Token" space.<br>
Make sure to enable EVERY priveledged gateway intent or the bot will not work.
### Webhook
Follow [this tutorial](https://youtu.be/fKksxz2Gdnc?t=13&si=7FdMdJW6SNqSMZ4N) to create a discord webhook and paste the webhook url into the "Webhook URL" space.
### Server Sniper
Authorization Key:
1. Activate developer tools on your discord client by pressing Ctrl + Shift + I and navigate to "Network" tab
2. Enable Fetch/XHR
3. Click on any channel from any server
4. Click on the messages?limit=50 option
5. Right click and copy as fetch, paste into a notepad
6. Copy the text in the authorization field, it should start with MTA
7. Paste it into the Authorization Key field in the Server Sniper config editor
Channel Link:
1. Go to any discord server and right click the channel you want to monitor and snipe servers from, click copy link
2. Paste that link into the Chanel Link field in the Server Sniper config editor

## Credits
### Owner
- vexthecoder (Basically Everything)
### Contributers
- Noteab and Their Team (Original Source Code)

## To-Do
### v1.0.3
1. Multi-channel sniping support.
### v1.1
1. Finalize AutoClicker module.
2. More Discord commands.
3. Cutscene detection? (most likely not)

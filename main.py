import keep_alive
import os
import TABot

client = TABot.MyClient()

#keeps the bot running on the server
keep_alive.keep_alive()

client.run(os.environ['token'])
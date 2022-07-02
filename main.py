import keep_alive
import os
import Bot
import redis

client = Bot.MyClient()

#keeps the bot running on the server
keep_alive.keep_alive()

client.run(os.environ['token'])
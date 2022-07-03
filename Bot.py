from multiprocessing.sharedctypes import Value
import os
import random
import discord
from discord.ext import tasks
import redis
from httplib2 import Http
import threading
import asyncio

import MACDTrader
import WeatherBot
import TrackBot
import ListBot

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.r = redis.from_url(os.environ.get("REDIS_URL"))
        
        self.products = []

        if(self.r.exists("products")):
            self.products = self.r.lrange("products", 0, -1)
        
        for index in range(len(self.products)):
            self.products[index] = self.products[index].decode("utf-8")

        self.trader = MACDTrader.MACDTrader(products=self.products)
        
        self.weather = WeatherBot.WeatherBot()
        
        self.saved_locations = {}

        if(self.r.exists("saved_locations")):
            self.saved_locations_bytes = self.r.hgetall("saved_locations")
            for key in self.saved_locations_bytes.keys():
                self.saved_locations[key.decode("utf-8")] = self.saved_locations_bytes[key].decode("utf-8")

        self.responses_affirmative = [
            "It is certain", "It is decidedly so", "Without a doubt",
            "Yes definitely", "Yes"
        ]
        self.responses_non_committal = [
            "Ask again later please", "Better not tell you now",
            "Concentrate and ask again", "You already know the answer", "Maybe"
        ]
        self.responses_negative = [
            "Don't count on it", "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful", "No"
        ]
        
        self.user_added = []

        if(self.r.exists("user_added")):
            self.user_added = [item.decode("utf-8") for item in self.r.lrange("user_added", 0, -1)]
        
        # for index in range(len(self.user_added)):
        #     self.user_added[index] = self.user_added[index].decode("utf-8")

        self.lists = []

        if(self.r.exists("discord_lists")):
            self.lists = []
            for item in self.r.lrange("discord_lists", 0, -1):
                self.lists.append(ListBot.from_string(item.decode("utf-8")))
        
        self.users_creating_list = {}
        self.users_finishing_list = []
        self.users_selected = {}

        self._MACD_ADD_CMD = "$signal add "
        self._MACD_REM_CMD_1 = "$signal rem "
        self._MACD_REM_CMD_2 = "$signal remove "

        self._8_BALL_ADD_CMD = "8!add "
        self._8_BALL_REM_CMD = "8!rem "
        self._8_BALL_RESPONSES_CMD = "8!responses"
        self._8_BALL_BALL_CMD = "8!ball"
        
        self._WEATHER_CMD = "?weather "
        self._WEATHER_SAVE_CMD = "?weather save "
        self._WEATHER_DELETE_CMD = "?weather delete "
        self._WEATHER_SAVED_CMD = "?weather check saved"
        self._WEATHER_SHORTCUT_CMD = "?"

        self._LIST_CREATE_CMD = "-list create"
        self._LIST_SHOW_CMD = "-list show"
        self._LIST_SELECT_CMD = "-list select "
        self._LIST_DESELECT_CMD = "-list deselect"
        self._LIST_DELETE_CMD = "-list delete "
        self._LIST_ADD_CMD = "++"
        self._LIST_REMOVE_CMD = "--"
        self._LIST_MODIFY_CMD = "+-"

        self._HELP_CMD = "!help"

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(name='!help', type=discord.ActivityType.listening))
        print(f'We have logged in as {self.user} (ID: {self.user.id})')

    #****help functions****
    async def embed(self, channel):
        embed=discord.Embed(title="Bot",
                            url="https://github.com/rmdluo/bot/",
                            description="Multipurpose discord bot!",
                            color=discord.Color.blurple())

        embed.add_field(name="__**8Ball**__",
                        value="Generates answers to questions.",
                        inline=False)
        
        embed.add_field(name=" - 8!ball <question>",
                        value="Asks the 8Ball a question.",
                        inline=False)
        
        embed.add_field(name=" - 8!add <response>",
                        value="Adds a response that the 8Ball can use.",
                        inline=False)
        
        embed.add_field(name=" - 8!rem <response>",
                        value="Removes a response from the user-added 8Ball responses.",
                        inline=False)
        
        embed.add_field(name=" - 8!responses",
                        value="Shows the possible 8Ball responses.",
                        inline=False)
        
        embed.add_field(name="__**WeatherBot**__",
                        value="Gets the weather!",
                        inline=False)
        
        embed.add_field(name=" - ?weather <location>",
                        value="Gets the current weather in the inputted location.",
                        inline=False)
        
        embed.add_field(name=" - ?weather save <save_name>=<location>",
                        value="Saves a location as save_name. Can be called with ?save_name afterwards.",
                        inline=False)
        
        embed.add_field(name=" - ?weather delete <save_name>",
                        value="Deletes a saved location.",
                        inline=False)
        
        embed.add_field(name=" - ?weather check saved",
                        value="Displays a list of saved locations.",
                        inline=False)

        embed.add_field(name="__**ListBot**__",
                        value="Creates lists",
                        inline=False)

        embed.add_field(name=" - -list create",
                        value="Activates list creation",
                        inline=False)

        embed.add_field(name=" - -list show <(optional) list num>",
                        value="(Default/Input = all) Shows all lists\n(Input = number) Shows the inputted list",
                        inline=False)

        embed.add_field(name=" - -list delete <list num>",
                        value="Deletes the list num-th list",
                        inline=False)

        embed.add_field(name=" - -list select <list num>",
                        value="""
                                Selects the list num-th list
                                **++<item>** - adds item to selected list
                                **--<item number>** - removes the item from the selected list
                                **+-<item number> <item>** - changes the item number to the new item
                              """,
                        inline=False)

        embed.add_field(name=" - -list deselect",
                        value="Deselects the list num-th list",
                        inline=False)
                
        await channel.send(embed=embed)

    async def on_message(self, message):
        #****start 8Ball Commands****

        if (message.content.startswith(self._8_BALL_BALL_CMD)):
            num = 0

            if (len(self.user_added) > 0):
                num = random.randrange(4)
            else:
                num = random.randrange(3)

            response_list = []

            if (num == 0):
                response_list = self.responses_affirmative
            elif (num == 1):
                response_list = self.responses_non_committal
            elif (num == 2):
                response_list = self.responses_negative
            elif (num == 3):
                response_list = self.user_added

            await message.channel.send(response_list[random.randrange(
                len(response_list))]
            )

        elif (message.content.startswith(self._8_BALL_ADD_CMD)):
            if (message.content[len(self._8_BALL_ADD_CMD):] == ""):
                await message.channel.send(
                    "No response argument present: please put the desired response after a space after 8!add"
                )
            else:
                response = message.content[len(self._8_BALL_ADD_CMD):]
                self.user_added.append(response)
                self.r.lpush("user_added", response)
                await message.channel.send("Response added!")

        elif (message.content.startswith(self._8_BALL_REM_CMD)):
            try:
                response = message.content[len(self._8_BALL_REM_CMD):]
                self.user_added.remove(response)

                if(self.r.lrem("user_added", 0, response) == 0):
                    raise(ValueError)
                
                await message.channel.send("Response removed!")

            except ValueError:
                await message.channel.send(
                    "You are trying to remove a preset response or your response was never added"
                )

        elif (message.content.startswith(self._8_BALL_RESPONSES_CMD)):
            res_str = ""

            for response in (self.responses_affirmative +
                             self.responses_non_committal +
                             self.responses_negative +
                             self.user_added):
                res_str = res_str + response + "\n"
                
            if(res_str == ""):
                await message.channel.send("No added responses...")
            else:
                await message.channel.send(res_str)

        #****end 8Ball Commands****
        
        #****start Weather commands****
            
        elif(message.content.startswith(self._WEATHER_SAVE_CMD)):
            try:
                if (message.content[len(self._WEATHER_SAVE_CMD):] == ""):
                    await message.channel.send(
                        "No response argument present: please put the desired response after a space after 8!add"
                    )
                else:
                    location = message.content[len(self._WEATHER_SAVE_CMD):].split("=")
                    self.saved_locations[location[0]] = location[1]
                    
                    self.r.hset("saved_locations", location[0], location[1])
                    
                    await message.channel.send("Location saved!")
            except IndexError:
                await message.channel.send("Enter arguments as save_name=location")
            
                
        elif(message.content.startswith(self._WEATHER_DELETE_CMD)):
            try:
                location = message.content[len(self._WEATHER_DELETE_CMD):]
                self.saved_locations.pop(location)
                
                self.r.hdel("saved_locations", location)

                await message.channel.send("Location deleted!")

            except KeyError:
                await message.channel.send(
                    "Location never saved :("
                )
                
        elif(message.content.startswith(self._WEATHER_SAVED_CMD)):
            saved = ""
            for key in self.saved_locations:
                saved = saved + key + " = " + self.saved_locations[key] + "\n"
            
            if(saved == ""):
                await message.channel.send("No saved locations :eyes:")
            else:
                await message.channel.send(saved)
            
        elif(message.content.startswith(self._WEATHER_CMD)):
            location = location = message.content[len(self._WEATHER_CMD):]
            if(location in self.saved_locations.keys()):
                location = self.saved_locations[location]

            try:
                location = location.split(",")
                await message.channel.send("```" + self.weather.get_current_weather(location[0].strip(), location[1].strip()) + "```")
            except IndexError:
                if(location == ""):
                    await message.channel.send("No location entered!")
                else:
                    await message.channel.send("```" + self.weather.get_current_weather(location) + "```")
                    
        elif(message.content.startswith(self._WEATHER_SHORTCUT_CMD)):
            location = message.content[len(self._WEATHER_SHORTCUT_CMD):]
            if(location in self.saved_locations.keys()):
                location = self.saved_locations[location]

                try:
                    location = location.split(",")
                    await message.channel.send("```" + self.weather.get_current_weather(location[0].strip(), location[1].strip()) + "```")
                except IndexError:
                    if(location == ""):
                        await message.channel.send("No location entered!")
                    else:
                        await message.channel.send("```" + self.weather.get_current_weather(location) + "```")       
            else:
                await message.channel.send("```Not a saved location!```")

        #****end Weather commands****

        #****start List commands
        
        elif(message.content.startswith(self._LIST_CREATE_CMD)):
            await message.channel.send("Enter the items for your list using the following format: \"-{item}\". When you're done, please send \"--stop\".")
            self.users_creating_list[message.author.display_name] = []

        elif(message.author.display_name in self.users_finishing_list):
            if(message.content.startswith("--")):
                l = ListBot.List(
                                    message.content[2:],
                                    message.author.display_name,
                                    items=self.users_creating_list[message.author.display_name]
                                )
                self.lists.append(l)
                self.r.lpush("discord_lists", l.to_string())
                await message.channel.send(l.to_output())

                self.users_finishing_list.remove(message.author.display_name)
                del self.users_creating_list[message.author.display_name]
        
        elif(message.author.display_name in self.users_creating_list.keys()):
            if(message.content.startswith("--stop")):
                await message.channel.send("What is the name of your list? Enter it as \"--{name}\".")
                self.users_finishing_list.append(message.author.display_name)
            elif(message.content.startswith("-")):
                self.users_creating_list[message.author.display_name].append(message.content[1:])
                await message.add_reaction("\U00002705")

        #TODO: display lists
        elif(message.content.startswith(self._LIST_SHOW_CMD)):
            arg = message.content[len(self._LIST_SHOW_CMD):].lower()
            if(arg == "" or arg == "all"):
                info_str = ""; i = 1
                for list in self.lists:
                    info_str += str(i) + ". " + list.get_display_string() + "\n"
                    i += 1
                await message.channel.send(info_str)
            else:
                try:
                    await message.channel.send(self.lists[int(arg) - 1].to_output())
                except ValueError:
                    await message.channel.send("Not a list -- check *-list show*")
            

        #TODO: delete lists
        elif(message.content.startswith(self._LIST_DELETE_CMD)):
            try:
                index = int(message.content[len(self._LIST_DELETE_CMD):]) - 1
                l = self.lists.pop(index)
                self.r.lrem("discord_lists", 0, l.to_string())
                await message.channel.send("List deleted:")
                await message.channel.send(l.to_output())
            except IndexError:
                await message.channel.send("not a list -- check *-list show*")

        #TODO: alter lists
        elif(message.content.startswith(self._LIST_SELECT_CMD)):
            try:
                list_index = int(message.content[len(self._LIST_SELECT_CMD):]) - 1
                await message.channel.send(self.lists[list_index].to_output())
                self.users_selected[message.author.display_name] = list_index
            except IndexError:
                await message.channel.send("not a list -- check *-list show*")

        elif(message.content.startswith(self._LIST_DESELECT_CMD)):
            if(message.author.display_name in self.users_selected.keys()):
                index = self.users_selected[message.author.display_name]
                await message.channel.send(self.lists[index].to_output())
                del self.users_selected[message.author.display_name]
            else:
                await message.channel.send("No list selected -- use *-list select {list number}*")


        #TODO: add to lists
        elif(message.content.startswith(self._LIST_ADD_CMD)):
            if(message.author.display_name in self.users_selected.keys()):
                index = self.users_selected[message.author.display_name]
                self.lists[index].add_item(message.content[len(self._LIST_ADD_CMD):])
                await message.add_reaction("\U00002705")
                self.r.lset("discord_lists", index, self.lists[index].to_string())
            else:
                await message.channel.send("Please select a list first -- *-list select {list number}*")
                
        elif(message.content.startswith(self._LIST_REMOVE_CMD)):
            if(message.author.display_name in self.users_selected.keys()):
                try:
                    await message.channel.send("Delete \"" + self.lists[self.users_selected[message.author.display_name]].get_item(int(message.content[len(self._LIST_REMOVE_CMD):]) - 1) + "\"? Yes/No")

                    def check(m):
                        return m.author.display_name == message.author.display_name and (m.content.lower() == "yes" or m.content.lower() == "no")

                    reply_message = await self.wait_for('message', check=check)

                    # reply_message = await self.wait_for('message')

                    # while(reply_message.author.display_name != message.author.display_name or (reply_message.content.lower() != "yes" and reply_message.content.lower() != "no")):
                    #     reply_message = await self.wait_for('message')

                    if reply_message.content.lower() == 'yes':
                        index = self.users_selected[message.author.display_name]
                        self.lists[index].remove_item(int(message.content[len(self._LIST_REMOVE_CMD):]) - 1)
                        await reply_message.add_reaction("\U00002705")
                        self.r.lset("discord_lists", index, self.lists[index].to_string())
                        # await message.channel.send(self.lists[index].to_output())
                    else:
                        await reply_message.add_reaction("\U00002705")
                except ValueError:
                    await message.channel.send("Please enter the item number, not the item")
            else:
                await message.channel.send("Please select a list first -- *-list select {list number}*")

        elif(message.content.startswith(self._LIST_MODIFY_CMD)):
            if(message.author.display_name in self.users_selected.keys()):
                message_info = message.content[len(self._LIST_MODIFY_CMD):].split(" ")
                self.lists[int(message_info[0]) - 1] = message_info[1]
                await message.add_reaction("\U00002705")
            else:
                await message.channel.send("Please select a list first -- *-list select {list number}*")

        #****end List commands****
        
        if(message.content==self._HELP_CMD):
            await self.embed(message.channel)
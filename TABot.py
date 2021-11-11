import os
import random
import discord
from discord.ext import tasks

import MACDTrader
import WeatherBot

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.products = []

        with open("products.txt", "r") as input:
            for line in input:
                self.products.append(line.strip("\n"))

        self.trader = MACDTrader.MACDTrader(products=self.products)
        
        self.weather = WeatherBot.WeatherBot()
        
        self.saved_locations = {}
        
        with open("saved_locations.txt", "r") as input:
            for line in input:
                if(line.strip() != ""):
                    line_info = line.strip().split("=") 
                    self.saved_locations[line_info[0]] = line_info[1]

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

        with open("responses.txt", "r") as input:
            for line in input:
                self.user_added.append(line.strip("\n"))

        self._8_BALL_ADD_CMD = "8!add "
        self._8_BALL_REM_CMD = "8!rem "
        self._8_BALL_RESPONSES_CMD = "8!responses "
        self._8_BALL_BALL_CMD = "8!ball "
        
        self._WEATHER_CMD = "?weather "
        self._WEATHER_SAVE_CMD = "?weather save "
        self._WEATHER_DELETE_CMD = "?weather delete "
        self._WEATHER_SAVED_CMD = "?weather check saved"

        self.trader_signals.start()

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(name='***Not yet implemented! !help', type="watching"))
        print(f'We have logged in as {self.user} (ID: {self.user.id})')

    #****MACDTrader functions****

    @tasks.loop(seconds=60)
    async def trader_signals(self):
        channel = self.get_channel(int(os.environ['channel_id']))

        signals = self.trader.get_signals()

        for signal in signals:
            await channel.send(signal)

    @trader_signals.before_loop
    async def before_signals(self):
        await self.wait_until_ready()

    #****end MACDTrader functions****

    async def on_message(self, message):

        # ****start MACDTrader commands for the bot****
        if (message.content.startswith('$signal add')):
            try:
                self.trader.add_product(message.content.split(" ")[2])
                await message.channel.send("Product added!")
            except IndexError:
                await message.channel.send(
                    "Please add the product symbol and ensure that it is separated from the command using a space."
                )
            except ValueError:
                await message.channel.send("Invalid product")
            except Exception:
                await message.channel.send("Product already added!")

        elif (message.content.startswith('$signal remove')
              or message.content.startswith("$signal rem")):
            try:
                self.trader.remove_product(message.content.split(" ")[2])
                await message.channel.send("Product removed!")
            except IndexError:
                await message.channel.send(
                    "Please add the product symbol and ensure that it is separated from the command using a space."
                )
            except ValueError:
                await message.channel.send(
                    "This product was not added before ;-;")

        elif (message.content.startswith('$signal products')):
            await message.channel.send(self.trader.get_products_str())

        #****end MACDTrader Commands****

        #****start 8Ball Commands****

        elif (message.content.startswith(self._8_BALL_BALL_CMD)):
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
                await message.channel.send("Response added!")

                f = open("responses.txt", "a")

                f.write(response + "\n")

                f.close()

        elif (message.content.startswith(self._8_BALL_REM_CMD)):
            try:
                response = message.content[len(self._8_BALL_REM_CMD):]
                self.user_added.remove(response)

                await message.channel.send("Response removed!")

                with open("products.txt", "r") as input:
                    with open("temp.txt", "w") as output:
                        # iterate all lines from file
                        for line in input:
                            # if text matches then don't write it
                            if line.strip("\n") != response:
                                output.write(line)
            except ValueError:
                await message.channel.send(
                    "You are trying to remove a preset response or your response was never added"
                )

        elif (message.content.startswith(self._8_BALL_RESPONSES_CMD)):
            res_str = ""

            for response in (self.responses_affirmative +
                             self.responses_non_committal +
                             self.responses_negative + self.user_added):
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
                    
                    self.weather.save_location(location)
                    
                    await message.channel.send("Location saved!")
            except IndexError:
                await message.channel.send("Enter arguments as save_name=location")
            
                
        elif(message.content.startswith(self._WEATHER_DELETE_CMD)):
            try:
                location = message.content[len(self._WEATHER_DELETE_CMD):]
                self.saved_locations.pop(location)

                await message.channel.send("Location deleted!")

                with open("saved_locations.txt", "r") as input:
                    with open("temp.txt", "w") as output:
                        # iterate all lines from file
                        for line in input:
                            # if text matches then don't write it
                            if not (location in line):
                                output.write(line)
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
            try:
                location = message.content[len(self._WEATHER_CMD):].split(", ")
                await message.channel.send("```" + self.weather.get_current_weather(location[0], location[1]) + "```")
            except IndexError:
                location = message.content[len(self._WEATHER_CMD):]
                
                if(location == ""):
                    await message.channel.send("No location entered!")
                elif(location in self.saved_locations.keys()):
                    await message.channel.send("```" + self.weather.get_current_weather(self.saved_locations[location]) + "```")
                else:
                    await message.channel.send("```" + self.weather.get_current_weather(location) + "```")

        #****end Weather commands****

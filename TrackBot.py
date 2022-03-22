from json import dumps
from httplib2 import Http #httplib2-0.20.4
from discord import Message

class TrackBot:
  def __init__(self, webhook_url):
    self.webhook_url = webhook_url
    self.channels = []
    
  def add_channel(self, channel):
    self.channels.append(channel)
    
  def send_notif(self, message):
    if(message.channel in self.channels):
      http_obj = Http
      
      message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

      http_obj.request(
        uri = self.webhook_url,
        method="POST",
        headers=message_headers,
        body=dumps("Message from " + message.author.display_name + " in " + message.channel)
      )
  
  def del_channel(self, channel):
    self.channels.remove(channel)

from flask import Flask
from multiprocessing import Process

app = Flask("")

@app.route("/")
def main():
  return "Your bot is up!"

def run():
  app.run(host="0.0.0.0", port=8080)

def keep_alive():
  global server
  server = Process(target=run)
  server.start()

def kill():
  global server
  server.terminate()

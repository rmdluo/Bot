import pandas_ta as ta
import yfinance as yf
import os

class MACDTrader:
    def __init__(self, products, fast=12, slow=26, signal=9,
                ema_period=200, data_period="5d", data_interval="5m"):

        self.products = products
        self.product_trades = {}

        for product in products:
          self.product_trades[product] = "closed"
        
        self.strategy = ta.Strategy(name = "MACD and EMA",
                                    description = "uses 200EMA and MACD 12 26 9",
                                    ta=[
                                        {"kind": "macd", "fast": fast, "slow": slow, "signal": signal},
                                        {"kind": "ema", "length": ema_period}
                                    ]
                        )

        self.ema_period = ema_period

        self.period = data_period
        self.interval = data_interval

    def get_product_data(self, product_name):
        return yf.download(tickers = product_name, period = self.period, interval = self.interval) #uses yf ticker, returns a dataframe

    def get_signals(self):
        signals = []

        for product in self.products:
            df = self.get_product_data(product)

            if(not df.empty):
              df.ta.strategy(self.strategy, close = "Close")

              df["EMA200"] = ta.ema(df["Close"], length=self.ema_period)

              price = df["Close"][-1]
              ema = df["EMA200"][-1]

              macd = df["MACD_12_26_9"]
              macds = df["MACDs_12_26_9"]

              macd1 = macd[-1]
              macds1 = macds[-1]

              macd2 = macd.iloc[-2]
              macds2 = macds.iloc[-2]

              macd_diff_1 = macd1 - macds1 #macd - signal: if macd > signal, positive. if macd < signal, negative.
              macd_diff_2 = macd2 - macds2

              if(self.product_trades[product] == "closed" and macd_diff_1 > 0 and macd_diff_2 < 0 and macd1 < 0 and price > ema):
                  self.product_trades[product] = "open"
                  signals.append("Buy:"+ product)
              elif(self.product_trades[product] == "open" and macd_diff_1 < 0 and macd_diff_2 > 0):
                  self.product_trades[product] = "closed"
                  signals.append("Sell:"+ product)

        return signals

    def add_product(self, product):
        if(yf.download(tickers = product, period = self.period, interval = self.interval).empty):
            raise(ValueError)
        else:
            if(product in self.products):
                raise(Exception)
            else:
                self.products.append(product)
                self.product_trades[product] = "closed"
                
                f = open("products.txt", "a")

                f.write(product + "\n")

                f.close()

    def remove_product(self, product):
        try:
            self.products.remove(product)
            self.product_trades.pop(product)

            with open("products.txt", "r") as input:
                with open("temp.txt", "w") as output:
                 # iterate all lines from file
                    for line in input:
                     # if text matches then don't write it
                         if line.strip("\n") != product:
                              output.write(line)

            # replace file with original name
            os.replace('temp.txt', 'products.txt')
        except ValueError:
            raise(ValueError)
        except KeyError:
            raise(ValueError)

    def get_products_str(self):
        str = ""
        for product in self.products:
            str = str + product + "\n"

        return str

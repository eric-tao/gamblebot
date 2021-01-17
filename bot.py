#!/bin/python3

import discord
import sqlite3
import datetime
import requests
import re
import sys

class DBHelper:
    def __init__(self,dbname='db.sqlite3'):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def setup(self):
        tables = [ "crypto_prices", "stock_prices" ]
        for table in tables:
            stmt = 'CREATE TABLE IF NOT EXISTS %s (date text, name text, price real)'%(table)
            self.conn.execute(stmt)
            stmt = 'CREATE INDEX IF NOT EXISTS %s_date_index ON %s (date)'%(table,table)
            self.conn.execute(stmt)
            stmt = 'CREATE INDEX IF NOT EXISTS %s_name_index ON %s (name)'%(table,table)
            self.conn.execute(stmt)
            self.conn.commit()

    def add_item(self,table,values=()):
        stmt = 'INSERT INTO %s (date,name,price) VALUES(?,?,?)'%(table)
        args = values
        if len(args) == 3:
            self.conn.execute(stmt,args)
            self.conn.commit()
        else:
            print("Refusing to insert due to wrong number of args")

    def get_item_by_time(self,table,time):
        stmt = 'SELECT * FROM %s WHERE date > ? ORDER BY date DESC LIMIT 1'%(table)
        args = (time.isoformat(sep=' '),)
        arr = self.conn.execute(stmt,args).fetchall()
        self.conn.commit()
        return arr

class MyClient(discord.Client):
    async def on_ready(self):
        self.db = DBHelper()
        self.db.setup()
        self.coindesk_api = "https://api.coindesk.com/v1/bpi/currentprice.json"
        self.time_delay = 5
        print('Logged on as', self.user)

    def get_cached_btc_price(self):
        now = datetime.datetime.now()
        cache_time = now - datetime.timedelta(minutes=self.time_delay)
        item = self.db.get_item_by_time("crypto_prices",cache_time)
        if len(item) == 0:
            request = requests.get(self.coindesk_api)
            while request.status_code != 200:
                sleep(10)
                request = requests.get(self.coindesk_api)
            time = datetime.datetime.fromisoformat(request.json()['time']['updatedISO'])
            usd_rate = request.json()['bpi']['USD']['rate_float']
            self.db.add_item("crypto_prices",(time,'BTC',usd_rate))
            return time,usd_rate
        else:
            time,name,price = item[0]
            time = datetime.datetime.fromisoformat(time)
            return time,price

    async def on_message(self,message):
        if message.author == self.user:
            return
        elif re.match(r'^gamble\b', message.content) is not None:
            if len(message.content.split()) == 1:
                await message.channel.send("Subcommands supported:\n```btc: display price of BTC in the past 15 min\n```")
            elif message.content.split()[1] == 'btc':
                time,price =  self.get_cached_btc_price()
                embed = discord.Embed()
                embed.description = "Powered by [CoinDesk](https://www.coindesk.com/price/bitcoin)"
                content = "The price of BTC at %s was %s USD\nThis bot will only query the price if cached data is older than %s minutes to avoid overuse of the API."%(time.ctime(),price,str(self.time_delay))
                await message.channel.send(content=content,embed=embed)
            else:
                await message.channel.send("Subcommands supported:\nbtc: display price of BTC in the past 15 min\n")
        elif message.content == "ping":
            await message.channel.send('pong')


client = MyClient()
try:
    client.run('insert_token_here')
except:
    e = sys.exc_info()[0]
    print(e)

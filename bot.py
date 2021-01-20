#!/bin/python3

import discord
import sqlite3
import datetime
import requests
import re
import sys
import dice
import os

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

    def add_crypto_index(self,table,values=()):
        stmt = 'INSERT INTO %s (name) VALUES(?)'%(table)
        args = values
        if len(args) == 1:
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
        self.coincap_api = "api.coincap.io/v2/asset/"
        self.time_delay = 5
        self.commands_msg = "Subcommands supported:\n```btc: display price of BTC in the past 15 min\nroll: with a xdy argument, roll x dice\n```"
        print('Logged on as', self.user)

    def get_asset_price(self, asset):
        now = datetime.datetime.now()
        requestString = self.coincap_api + asset
        request = requests.get(requestString)
        while request.status_code != 200:
            sleep(10)
            request = requests.get(requestString)
        time = now
        usd_rate = request.json()['data']['priceUsd']
        return usd_rate

    @bot.command(name="crypto")
    async def _crypto(self, arg1):
        price = get_asset_price(arg1)
        embed = discord.Embed()
        embed.description = "Powered by CoinCap"
        content = "The price of %s is %s USD"%(arg1,price)
        await message.channel.send(content=content,embed=embed)

    async def on_message(self,message):
        if message.author == self.user:
            return
        elif re.match(r'^gamble\b', message.content) is not None:
            if len(message.content.split()) == 1:
                await message.channel.send(self.commands_msg)
            # elif message.content.split()[1] == 'btc':
            #     time,price =  self.get_cached_btc_price()
            #     embed = discord.Embed()
            #     embed.description = "Powered by [CoinDesk](https://www.coindesk.com/price/bitcoin)"
            #     content = "The price of BTC at %s was %s USD\nThis bot will only query the price if cached data is older than %s minutes to avoid overuse of the API."%(time.ctime(),price,str(self.time_delay))
            #     await message.channel.send(content=content,embed=embed)
            elif message.content.split()[1] == 'roll':
                if len(message.content.split()) == 2:
                     await message.channel.send("Roll usage:\n```gamble roll xdy: rolls x dice with a range from 1 to y```")
                elif re.match(r'^\d+d\d+$',message.content.split()[2]) is not None:
                    string = message.content.split()[2]
                    x,y = string.split("d")
                    if x == 1:
                        await message.channel.send("Rolling %s die with %s faces each...\n%s!"%(x,y,sum(dice.roll(string))))
                    else:
                        await message.channel.send("Rolling %s dice with %s faces each...\n%s!"%(x,y,sum(dice.roll(string))))
                else:
                    await message.channel.send("Roll usage:\n```gamble roll xdy: rolls x dice with a range from 1 to y```")
            else:
                await message.channel.send(self.commands_msg)
        elif message.content == "ping":
            await message.channel.send('pong')


client = MyClient()
try:
    client.run(os.environ.get('DISCORD_TOKEN'))
except:
    e = sys.exc_info()[0]
    print(e)

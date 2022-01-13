import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import has_permissions
with open("cfg", "r") as file:
    cfg = eval(file.read())
TOKEN = cfg["token"]
PREFIX = cfg["prefix"]
INTENTS = discord.Intents.default()
INTENTS.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS)

guild_settings = {}
# guild_channels_cache = {}
with open("blacklist") as file:
    blacklisted_users = eval(file.read())
with open("whitelist") as file:
    whitelisted = eval(file.read())

def load_guild_settings(id):
    settings = {
        "mod_reports":0,
        "log_all":False
    }
    try:
        with open("GuildData/" + str(id), "r") as file:
            settings = eval(file.read())
    except FileNotFoundError:
        with open("GuildData/" + str(id), "w") as file:
            file.write(str(settings))
    guild_settings[id] = settings
    return guild_settings[id]

def save_guild_settings(id):
    with open("GuildData/" + str(id), "w") as file:
        file.write(str(guild_settings[id]))

def save_blacklist():
    with open("blacklist", "w") as file:
        file.write(str(blacklisted_users))

@bot.event
async def on_guild_join(guild):
    load_guild_settings(guild.id)

@bot.event
async def on_member_join(member):
    for user in blacklisted_users:
        if(member.id == user):
            try:
                await send_blacklist_message(member, member.guild, blacklisted_users[user]["reason"])
            except Exception as e:
                print(member.guild.name + ": " + str(e))

@bot.command()
@has_permissions(ban_members=True)  
async def unblacklist(ctx, id):
    if(verify(ctx)):
        await ctx.send("This guild is not whitelisted, please contact bleedn#3333 for verification")
        return
    if(len(ctx.message.mentions)>0):
        try:
            blacklisted_users.pop(ctx.message.mentions[0].id)
            await ctx.send("User removed from blacklist.")
        except:
            await ctx.send("User not found in blacklist.")
    else:
        try:
            blacklisted_users.pop(int(id))
            await ctx.send("User removed from blacklist.")
        except:
            await ctx.send("User not found in blacklist.")
    save_blacklist()

@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name}')
    print(f'With ID: {bot.user.id}')
    for guild in bot.guilds:
        load_guild_settings(guild.id)
        print(guild.name + " loaded.")

@bot.command()
@has_permissions(ban_members=True)  
async def logchannel(ctx, toggle="nil"):
    if(toggle == "on"):
        guild_settings[ctx.guild.id]["log_all"] = ctx.channel.id
        await ctx.send("Blacklist log channel has been set.")
        save_guild_settings(ctx.guild.id)
    elif(toggle == "off"):
        guild_settings[ctx.guild.id]["log_all"] = False
        await ctx.send("Blacklist log channel has been removed.")
        save_guild_settings(ctx.guild.id)
    else:
        await ctx.send("Invalid command syntax: Please use !logchannel (on/off)")

@bot.command()
@has_permissions(ban_members=True)  
async def blacklistchannel(ctx, toggle="nil"):
    if(toggle == "on"):
        g=ctx.guild
        ids = [m.id for m in g.members]
        guild_settings[ctx.guild.id]["mod_reports"] = ctx.channel.id
        save_guild_settings(ctx.guild.id)
        await ctx.send("Blacklist message channel has been set.")
        for id in ids:
            for user in blacklisted_users.keys():
                if(id == user):
                    await send_blacklist_message(g.get_member(id), g, blacklisted_users[id]["reason"])        # if(id in b_ids):
    elif(toggle == "off"):
        g=ctx.guild
        guild_settings[ctx.guild.id]["mod_reports"] = 0
        save_guild_settings(ctx.guild.id)
        await ctx.send("Blacklist message channel has been removed.")
    else:
        await ctx.send("Invalid command syntax: Please use !blacklistchannel (on/off)")

@bot.command()
@has_permissions(ban_members=True)  
async def blacklist(ctx, user, *reason):
    if(verify(ctx)):
        await ctx.send("This guild is not whitelisted, please contact bleedn#3333 for verification")
        return
    reason = " ".join(reason)
    if(reason == ""):
        await ctx.send("You must provide a reason.")
        return
    if(len(ctx.message.mentions) > 0):
        try:
            test = blacklisted_users[ctx.message.mentions[0].id]
            await ctx.send("User already exists in blacklist.")
            return
        except KeyError:
            await add_to_blacklist(ctx.message.mentions[0].id, reason, ctx.guild, ctx)
            await log_blacklist(ctx.message.author.name + "#" + ctx.message.author.discriminator, ctx.message.mentions[0].id, reason)
    else:
        try:
            user_id = int(user)
            try:
                test = blacklisted_users[user_id]
                await ctx.send("User already exists in blacklist.")
                return
            except(KeyError):
                await add_to_blacklist(user_id, reason, ctx.guild, ctx)
                await log_blacklist(ctx.message.author.name + "#" + ctx.message.author.discriminator, user_id, reason)
        except:
            await ctx.send("Invalid user. (Format: !blacklist mention/userid reason)")
            return
    await ctx.send("User added to blacklist.")
            
async def add_to_blacklist(id, reason, guild, ctx):
    blacklisted_users[id] = {   
        "guild":guild.name,
        "reason":reason
    }
    save_blacklist()
    for guild in bot.guilds:
        for member in guild.members:
            if(member.id == id):
                await send_blacklist_message(member, guild, reason)

async def send_blacklist_message(member, guild, reason):
    embed = discord.Embed.from_dict({
        "title":"New Blacklisted Member Found",
        "description":"{0}\nID: {1}\nReason: {2}\nGuild: {3}".format(member.mention,member.id,reason,guild.name),
        "color":discord.Colour.red().value
    })
    embed.set_thumbnail(url=str(member.avatar_url))
    if(guild_settings[guild.id]['mod_reports'] != 0):
        print(guild_settings[guild.id]['mod_reports'])
        g = guild.get_channel(guild_settings[guild.id]["mod_reports"])
        try:
            await g.send(embed=embed)
        except Exception as e:
            print(guild.name + ": " + str(e))

async def log_blacklist(author, member, reason):
    # print("blacklist log" + author + str(member)+reason)
    embed = discord.Embed.from_dict({
        "title":str(author)+" has blacklisted id:"+str(member),
        "description":"Reason: " + reason,
        "color":discord.Colour.red().value
    })
    for g in guild_settings.keys():
        if(guild_settings[g]['log_all'] != False):
            g_handle = bot.get_guild(g)
            # print(guild_settings[g]['log_all'])
            c_handle = g_handle.get_channel(guild_settings[g]['log_all'])
            try:
                await c_handle.send(embed=embed)
            except Exception as e:
                print(g_handle + ": " + str(e))

@bot.command()
async def whitelist(ctx, server_id):
    if(not (ctx.message.author.id==442425669276663809 or ctx.message.author.id==251132701917184000)):
        return
    if(server_id in whitelisted):
        await ctx.send("Server is already whitelisted")
        return
    whitelisted.append(int(server_id))
    with open("whitelist", "w") as file:
        file.write(str(whitelisted))
    await ctx.send("Server id has been added to the whitelist")

def verify(ctx):
    id = ctx.guild.id
    if(id in whitelisted):
        return False
    else:
        return True

bot.run(TOKEN)
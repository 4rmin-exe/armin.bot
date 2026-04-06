import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["arminbot"]

# Collections
warns_col = db["warns"]
logs_col = db["logs"]
prefix_col = db["prefix"]
tickets_col = db["tickets"]

# ======= WARNS =======

def get_warns(user_id: str):
    doc = warns_col.find_one({"_id": user_id})
    return doc["count"] if doc else 0

def set_warns(user_id: str, count: int):
    warns_col.update_one({"_id": user_id}, {"$set": {"count": count}}, upsert=True)

# ======= LOGS =======

def get_logs(guild_id: str):
    doc = logs_col.find_one({"_id": guild_id})
    return doc["channels"] if doc else {}

def set_log(guild_id: str, categorie: str, salon_id: int):
    logs_col.update_one(
        {"_id": guild_id},
        {"$set": {f"channels.{categorie}": salon_id}},
        upsert=True
    )

# ======= PREFIX =======

def get_prefix(guild_id: str):
    doc = prefix_col.find_one({"_id": guild_id})
    return doc["prefix"] if doc else "+"

def set_prefix(guild_id: str, prefix: str):
    prefix_col.update_one({"_id": guild_id}, {"$set": {"prefix": prefix}}, upsert=True)

# ======= TICKETS =======

def get_tickets(guild_id: str):
    doc = tickets_col.find_one({"_id": guild_id})
    return doc if doc else {"_id": guild_id, "roles": {}, "open": {}}

def set_ticket_role(guild_id: str, categorie: str, role_id: int):
    tickets_col.update_one(
        {"_id": guild_id},
        {"$set": {f"roles.{categorie}": role_id}},
        upsert=True
    )

def open_ticket(guild_id: str, user_id: str, salon_id: int):
    tickets_col.update_one(
        {"_id": guild_id},
        {"$set": {f"open.{user_id}": salon_id}},
        upsert=True
    )

def close_ticket(guild_id: str, user_id: str):
    tickets_col.update_one(
        {"_id": guild_id},
        {"$unset": {f"open.{user_id}": ""}},
        upsert=True
    )
# ======= OWNERS =======

def get_owners(guild_id: str):
    doc = db["owners"].find_one({"_id": guild_id})
    return set(doc["ids"]) if doc else set()

def add_owner(guild_id: str, user_id: int):
    db["owners"].update_one(
        {"_id": guild_id},
        {"$addToSet": {"ids": user_id}},
        upsert=True
    )

def remove_owner(guild_id: str, user_id: int):
    db["owners"].update_one(
        {"_id": guild_id},
        {"$pull": {"ids": user_id}}
    )

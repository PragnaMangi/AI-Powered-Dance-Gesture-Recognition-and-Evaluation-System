import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")

if not uri:
    print("❌ MONGODB_URI not found in .env")
    exit()

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)

    # Test connection
    client.admin.command("ping")

    print("✅ MongoDB Atlas connection successful!")

except Exception as e:
    print("❌ MongoDB connection failed:")
    print(e)
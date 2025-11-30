"""Database connections"""
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from .config import settings

# MongoDB
mongodb_client: AsyncIOMotorClient = None
database = None

# Redis
redis_client: redis.Redis = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongodb_client, database
    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = mongodb_client[settings.MONGO_DB_NAME]
    print(f"✅ Connected to MongoDB: {settings.MONGO_DB_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("❌ Closed MongoDB connection")


async def connect_to_redis():
    """Connect to Redis"""
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    await redis_client.ping()
    print(f"✅ Connected to Redis")


async def close_redis_connection():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        print("❌ Closed Redis connection")


def get_database():
    """Get database instance"""
    return database


def get_redis():
    """Get Redis client"""
    return redis_client

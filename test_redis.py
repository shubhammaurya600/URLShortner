import redis

url = "rediss://default:gQAAAAAAASFJAAIgcDJjOTJmY2VmYjVlM2E0MzhhYmNlYzE4ZmM1MjJlZWNlMw@chief-donkey-74057.upstash.io:6379"
try:
    client = redis.Redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=False,
    )
    client.ping()
    print("Connection successful!")
except Exception as e:
    print(f"Error: {type(e).__name__} - {e}")

import requests
import redis
import json
import openai
from functools import wraps

RAPID_API_KEY = ''
openai.api_key = ""

# Initialize Redis connection
REDIS_EXPIRATION = 86400 * 31  # 31 days in seconds
redis_client = redis.Redis(host='localhost', port=6379, db=0)


def cache_response(format_response='json'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a unique cache key based on the function name and arguments
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Check if the response is cached in Redis
            cached_response = redis_client.get(cache_key)
            if cached_response:
                # If found in cache, return the cached response
                if format_response == 'json':
                    return json.loads(cached_response)
                elif format_response == 'markdown':
                    return json.loads(cached_response)  # Decode and load the tuple

            # If not in cache, execute the function (i.e., make the API call)
            result = func(*args, **kwargs)

            # Cache the response in Redis, with an optional expiration time, only if result is valid
            if result and all(result):  # Ensure both markdown and links are non-empty
                if format_response == 'json':
                    redis_client.setex(cache_key, REDIS_EXPIRATION, json.dumps(result))
                elif format_response == 'markdown':
                    redis_client.setex(cache_key, REDIS_EXPIRATION, json.dumps(result))  # Serialize the tuple

            return result

        return wrapper
    return decorator

@cache_response(format_response='json')
def wayback_get_captures(search_url, year):
    url = "https://wayback-machine4.p.rapidapi.com/v1/calendar/"

    querystring = {"url": search_url, "date": str(year)}

    headers = {
        "x-rapidapi-key": "c224b198c7mshe78bd2a2adb2a32p1ecdf9jsnfaba96145ea6",
        "x-rapidapi-host": "wayback-machine4.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    return response.json()


@cache_response(format_response='json')
def wayback_get_content(search_url, date_str):
    url = "https://wayback-machine4.p.rapidapi.com/v1/content/"

    querystring = {"url": search_url, "date": date_str}

    headers = {
        "x-rapidapi-key": "c224b198c7mshe78bd2a2adb2a32p1ecdf9jsnfaba96145ea6",
        "x-rapidapi-host": "wayback-machine4.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    return response.json()


def gpt_request(prompt, max_tokens=1000, model="gpt-4o-mini"):
    completion = openai.chat.completions.create(
        model=model,  # Use the appropriate model (e.g., "gpt-4o-mini" or "gpt-3.5-turbo")
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": "You are a knowledgeable and helpful research assistant"},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content.strip()


def gpt_request_with_response_format(prompt, response_format, max_tokens=1000, model="gpt-4o-mini"):
    completion = openai.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format=response_format,
        messages=[
            {"role": "system", "content": "You are a knowledgeable and helpful research assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion


def gpt_conversation(history, max_tokens=1000, model="gpt-4o-mini"):
    completion = openai.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=history
    )
    return completion.choices[0].message.content.strip()
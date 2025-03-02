import tweepy

api_key = 'BKzLfLQbUn6E0UM9AJ6omkMAf'
api_key_secret = 'vvQ6qgWTt1XkWtCLH40Gj7XVJ3V8snSf68rjbt4QMFxrKODuhh'
access_token = '1895675937108475907-sNg2l3amD9TgBIzGi6sGeiNxY5s5sV'
access_token_secret = 'AGbhMVgJKwkIpLdyYsaMg6jUoOgeMf1BlkxWdp1xIlqU7'

client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_key_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

response = client.create_tweet(in_reply_to_tweet_id=1895703979012804757, text="testing reply")

print(response)
print(response.data)
print(f"https://twitter.com/user/status/{response.data['id']}")
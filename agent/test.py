import tweepy


bearer_token = ""

client = tweepy.Client("AAAAAAAAAAAAAAAAAAAAAKGKzgEAAAAA4LF%2FfWao3K0WR6eRqfCjTgMrM1s%3DghiDRg43rrFDcESEdsUJ5zREveld96K6LJMx2fVjG6mXckTSzz")

# Get User's Mentions

# This endpoint/method returns Tweets mentioning a single user specified by the
# requested user ID

user_id = 1895675937108475907

response = client.get_users_mentions(user_id, since_id=1895703979012804757)

# By default, only the ID and text fields of each Tweet will be returned
for tweet in response.data:
    print(tweet.id)
    print(tweet.text)

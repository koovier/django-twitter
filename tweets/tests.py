from testing.testcases import TestCase
from tweets.services import TweetService


class TweetServiceTests(TestCase):

    def setUp(self):
        super(TweetServiceTests, self).setUp()
        self.linghu = self.createUser('linghu')

    def test_get_user_tweets(self):
        tweet_ids = []
        for i in range(3):
            tweet = self.createTweet(self.linghu, 'tweet {}'.format(i))
            tweet_ids.append(tweet.id)
        tweet_ids = tweet_ids[::-1]

        # cache miss
        tweets = TweetService.get_cached_tweets(self.linghu.id)
        self.assertEqual([t.id for t in tweets], tweet_ids)

        # cache hit
        tweets = TweetService.get_cached_tweets(self.linghu.id)
        self.assertEqual([t.id for t in tweets], tweet_ids)

        # cache updated
        new_tweet = self.createTweet(self.linghu, 'new tweet')
        tweets = TweetService.get_cached_tweets(self.linghu.id)
        tweet_ids.insert(0, new_tweet.id)
        self.assertEqual([t.id for t in tweets], tweet_ids)

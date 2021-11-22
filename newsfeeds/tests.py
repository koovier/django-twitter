from newsfeeds.hbase_models import HBaseNewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.tasks import fanout_newsfeeds_main_task
from testing.testcases import TestCase


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        super(NewsFeedServiceTests, self).setUp()
        self.linghu = self.createUser('linghu')
        self.dongxie = self.createUser('dongxie')

    def test_get_user_newsfeeds(self):
        newsfeed_row_keys = []
        for i in range(3):
            newsfeed = self.createNewsFeed(self.linghu, user=self.dongxie)
            newsfeed_row_keys.append(newsfeed.row_key)
        newsfeed_row_keys = newsfeed_row_keys[::-1]

        # cache miss
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual([n.row_key for n in newsfeeds], newsfeed_row_keys)

        # cache hit
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual([n.row_key for n in newsfeeds], newsfeed_row_keys)

        # cache updated
        new_newsfeed = self.createNewsFeed(self.linghu, user=self.linghu)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        newsfeed_row_keys.insert(0, new_newsfeed.row_key)
        self.assertEqual([n.row_key for n in newsfeeds], newsfeed_row_keys)


class NewsFeedTaskTests(TestCase):

    def setUp(self):
        super(NewsFeedTaskTests, self).setUp()
        self.linghu = self.createUser('linghu')
        self.dongxie = self.createUser('dongxie')

    def test_fanout_main_task(self):
        tweet = self.createTweet(self.linghu, 'tweet 1')
        self.createFriendship(self.dongxie, self.linghu)
        msg = fanout_newsfeeds_main_task(tweet.id, tweet.created_at_as_int, self.linghu.id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, len(HBaseNewsFeed.filter()))
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.createUser('user{}'.format(i))
            self.createFriendship(user, self.linghu)
        tweet = self.createTweet(self.linghu, 'tweet 2')
        msg = fanout_newsfeeds_main_task(tweet.id, tweet.created_at_as_int, self.linghu.id)
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, len(HBaseNewsFeed.filter()))
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 2)

        user = self.createUser('another user')
        self.createFriendship(user, self.linghu)
        tweet = self.createTweet(self.linghu, 'tweet 3')
        msg = fanout_newsfeeds_main_task(tweet.id, tweet.created_at_as_int, self.linghu.id)
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, len(HBaseNewsFeed.filter()))
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.dongxie.id)
        self.assertEqual(len(cached_list), 3)

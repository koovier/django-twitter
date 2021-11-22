from django.conf import settings
from rest_framework.test import APIClient
from testing.testcases import TestCase
from utils.paginations import EndlessPagination
from newsfeeds.services import NewsFeedService
from newsfeeds.hbase_models import HBaseNewsFeed


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        super(NewsFeedApiTests, self).setUp()
        self.linghu = self.createUser('linghu')
        self.linghu_client = APIClient()
        self.linghu_client.force_authenticate(self.linghu)

        self.dongxie = self.createUser('dongxie')
        self.dongxie_client = APIClient()
        self.dongxie_client.force_authenticate(self.dongxie)

        # create followings and followers for dongxie
        for i in range(2):
            follower = self.createUser('dongxie_follower{}'.format(i))
            self.createFriendship(from_user=follower, to_user=self.dongxie)
        for i in range(3):
            following = self.createUser('dongxie_following{}'.format(i))
            self.createFriendship(from_user=self.dongxie, to_user=following)

    def test_list(self):
        # 需要登录
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # 不能用 post
        response = self.linghu_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # 一开始啥都没有
        response = self.linghu_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)
        # 自己发的信息是可以看到的
        self.linghu_client.post(POST_TWEETS_URL, {'content': 'Hello World'})
        response = self.linghu_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)
        # 关注之后可以看到别人发的
        self.linghu_client.post(FOLLOW_URL.format(self.dongxie.id))
        response = self.dongxie_client.post(POST_TWEETS_URL, {
            'content': 'Hello Twitter',
        })
        posted_tweet_id = response.data['id']
        response = self.linghu_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.createUser('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            newsfeed = self.createNewsFeed(owner=self.linghu, user=followed_user)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.linghu_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)

        results = response.data['results']
        self.assertEqual(results[0]['created_at'], newsfeeds[0].created_at)
        self.assertEqual(results[1]['created_at'], newsfeeds[1].created_at)
        self.assertEqual(results[page_size - 1]['created_at'], newsfeeds[page_size - 1].created_at)

        # pull the second page
        response = self.linghu_client.get(NEWSFEEDS_URL, {'created_at__lt': newsfeeds[page_size - 1].created_at})
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        results = response.data['results']
        self.assertEqual(results[0]['created_at'], newsfeeds[page_size].created_at)
        self.assertEqual(results[1]['created_at'], newsfeeds[page_size + 1].created_at)
        self.assertEqual(results[page_size - 1]['created_at'], newsfeeds[2 * page_size - 1].created_at)

        # pull latest newsfeeds
        response = self.linghu_client.get(NEWSFEEDS_URL, {'created_at__gt': newsfeeds[0].created_at})
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        new_newsfeed = self.createNewsFeed(owner=self.linghu, user=followed_user)
        response = self.linghu_client.get(NEWSFEEDS_URL, {'created_at__gt': newsfeeds[0].created_at})
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['created_at'], new_newsfeed.created_at)

    def test_user_cache(self):
        self.assertEqual(self.linghu.username, 'linghu')
        self.createNewsFeed(self.dongxie, user=self.linghu, content='feed 0')
        self.createNewsFeed(self.dongxie, user=self.createUser('user1'), content='feed 1')
        self.createNewsFeed(self.dongxie, user=self.createUser('user2'), content='feed 2')
        self.createNewsFeed(self.dongxie, user=self.createUser('user3'), content='feed 3')
        self.createNewsFeed(self.dongxie, user=self.linghu, content='feed 00')

        response = self.dongxie_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'linghu')
        self.assertEqual(response.data['results'][1]['tweet']['user']['username'], 'user3')

        self.linghu.username = 'linghuchong'
        self.linghu.save()
        self.linghu.refresh_from_db()
        self.assertEqual(self.linghu.username, 'linghuchong')

        response = self.dongxie_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'linghuchong')
        self.assertEqual(response.data['results'][1]['tweet']['user']['username'], 'user3')

    def _paginate_to_get_newsfeeds(self, client):
        # paginate until the end
        response = client.get(NEWSFEEDS_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = settings.ENDLESS_PAGINATION_PAGE_SIZE
        users = [self.createUser('user{}'.format(i)) for i in range(5)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            feed = self.createNewsFeed(self.linghu, user=users[i % 5], content='feed{}'.format(i))
            newsfeeds.append(feed)
        newsfeeds = newsfeeds[::-1]

        # only cached list_limit objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        db_newsfeeds = HBaseNewsFeed.filter(prefix=(self.linghu.id,))
        self.assertEqual(len(db_newsfeeds), list_limit + page_size)

        results = self._paginate_to_get_newsfeeds(self.linghu_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].created_at, results[i]['created_at'])

        # a followed user create a new tweet
        self.createFriendship(self.linghu, self.dongxie)
        new_tweet = self.createTweet(self.dongxie, 'a new tweet')
        NewsFeedService.fanout_to_followers(new_tweet)
        results = self._paginate_to_get_newsfeeds(self.linghu_client)
        self.assertEqual(len(results), list_limit + page_size + 1)
        self.assertEqual(results[0]['tweet']['id'], new_tweet.id)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].created_at, results[i + 1]['created_at'])

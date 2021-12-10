from testing.testcases import TestCase
from newsfeeds.models import NewsFeed
from friendships.models import Friendship
from rest_framework.test import APIClient


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedTest(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.leonard = self.create_user('leonard', 'leonard@cit.edu')
        self.leonard_client = APIClient()
        self.leonard_client.force_authenticate(self.leonard)

        self.sheldon = self.create_user('sheldon', 'sheldon@cit.edu')
        self.sheldon_client = APIClient()
        self.sheldon_client.force_authenticate(self.sheldon)

        # create followings and followers for sheldon
        for i in range(2):
            follower = self.create_user('sheldon_follower{}'.format(i), 'test@gmail.com')
            Friendship.objects.create(from_user=follower, to_user=self.sheldon)
        for i in range(3):
            following = self.create_user('sheldon_following{}'.format(i), 'test@gmail.com')
            Friendship.objects.create(from_user=self.sheldon, to_user=following)

    def test_list(self):

        # 403 for not logged in
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)

        # 405 for using POST method
        response = self.leonard_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)

        # no newsfeed at the beginning
        response = self.leonard_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)

        # check own newsfeeds
        self.leonard_client.post(POST_TWEETS_URL, {'content': 'Hello World'})
        response = self.leonard_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)

        # able to see other's newsfeed after following
        self.leonard_client.post(FOLLOW_URL.format(self.sheldon.id))
        response = self.sheldon_client.post(POST_TWEETS_URL, {
            'content': 'Hello Twitter',
        })
        posted_tweet_id = response.data['id']
        response = self.leonard_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)



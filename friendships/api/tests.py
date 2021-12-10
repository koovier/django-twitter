from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.sheldon = self.create_user('sheldon')
        self.sheldon_client = APIClient()
        self.sheldon_client.force_authenticate(self.sheldon)

        self.leonard = self.create_user('leonard')
        self.leonard_client = APIClient()
        self.leonard_client.force_authenticate(self.leonard)

        # create followings and followers for sheldon
        for i in range(2):
            follower = self.create_user('sheldon_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.sheldon.id)
        for i in range(3):
            following = self.create_user('sheldon_following{}'.format(i))
            Friendship.objects.create(from_user=self.sheldon, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.leonard.id)

        # 403 for not logged in
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # 405 for not using POST method
        response = self.sheldon_client.get(url)
        self.assertEqual(response.status_code, 405)

        # 400 for follow oneself
        response = self.leonard_client.get(url)
        self.assertEqual(response.status_code, 405)

        # 201 for successfully follow
        response = self.sheldon_client.post(url)
        self.assertEqual(response.status_code, 201)

        # 201 for duplicated follow
        response = self.sheldon_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)

        # Create new data when follow back
        count = Friendship.objects.count()
        response = self.leonard_client.post(FOLLOW_URL.format(self.sheldon.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.leonard.id)

        # require login
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # 405 for using wrong method
        response = self.sheldon_client.get(url)
        self.assertEqual(response.status_code, 405)

        # 400 for unfollow own account
        response = self.leonard_client.post(url)
        self.assertEqual(response.status_code, 400)

        # successfully unfollow
        Friendship.objects.create(from_user=self.sheldon, to_user=self.leonard)
        count = Friendship.objects.count()
        response = self.sheldon_client.post(url)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)

        # return 200 if not following
        count = Friendship.objects.count()
        response = self.sheldon_client.post(url)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.sheldon.id)

        # 405 for using post method
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # 200 for using get method
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)
        # order by time, recent first
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertTrue(ts0 > ts1)
        self.assertTrue(ts1 > ts2)
        self.assertEqual(response.data['followings'][0]['user']['username'], 'sheldon_following2')
        self.assertEqual(response.data['followings'][1]['user']['username'], 'sheldon_following1')
        self.assertEqual(response.data['followings'][2]['user']['username'], 'sheldon_following0')

    def tess_followers(self):
        url = FOLLOWERS_URL.format(self.sheldon.id)

        # 405 for using post method
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # 200 for using get method
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)
        # order by time, recent first
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        self.assertTrue(ts0 > ts1)
        self.assertEqual(response.data['followings'][0]['user']['username'], 'sheldon_follower1')
        self.assertEqual(response.data['followings'][1]['user']['username'], 'sheldon_follower0')





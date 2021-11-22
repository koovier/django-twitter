from utils.paginations import EndlessPagination
from friendships.services import FriendshipService
from rest_framework.test import APIClient
from testing.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        super(FriendshipApiTests, self).setUp()
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

    def test_follow(self):
        url = FOLLOW_URL.format(self.linghu.id)

        # 需要登录才能 follow 别人
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # 要用 get 来 follow
        response = self.dongxie_client.get(url)
        self.assertEqual(response.status_code, 405)
        # 不可以 follow 自己
        response = self.linghu_client.post(url)
        self.assertEqual(response.status_code, 400)
        # follow 成功
        response = self.dongxie_client.post(url)
        self.assertEqual(response.status_code, 201)
        # 重复 follow 静默成功
        response = self.dongxie_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)
        # 反向关注会创建新的数据
        before_count = FriendshipService.get_following_count(self.linghu.id)
        response = self.linghu_client.post(FOLLOW_URL.format(self.dongxie.id))
        self.assertEqual(response.status_code, 201)
        after_count = FriendshipService.get_following_count(self.linghu.id)
        self.assertEqual(after_count, before_count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.linghu.id)

        # 需要登录才能 unfollow 别人
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # 不能用 get 来 unfollow 别人
        response = self.dongxie_client.get(url)
        self.assertEqual(response.status_code, 405)
        # 不能用 unfollow 自己
        response = self.linghu_client.post(url)
        self.assertEqual(response.status_code, 400)
        # unfollow 成功
        self.createFriendship(from_user=self.dongxie, to_user=self.linghu)
        before_count = FriendshipService.get_following_count(self.dongxie.id)
        response = self.dongxie_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        after_count = FriendshipService.get_following_count(self.dongxie.id)
        self.assertEqual(after_count, before_count - 1)
        # 未 follow 的情况下 unfollow 静默处理
        before_count = FriendshipService.get_following_count(self.dongxie.id)
        response = self.dongxie_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        after_count = FriendshipService.get_following_count(self.dongxie.id)
        self.assertEqual(before_count, after_count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.dongxie.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # 确保按照时间倒序
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'dongxie_following2',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'dongxie_following1',
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
            'dongxie_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.dongxie.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # 确保按照时间倒序
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'dongxie_follower1',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'dongxie_follower0',
        )

    def test_followers_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            follower = self.createUser('linghu_follower{}'.format(i))
            friendship = self.createFriendship(from_user=follower, to_user=self.linghu)
            friendships.append(friendship)
            if follower.id % 2 == 0:
                self.createFriendship(from_user=self.dongxie, to_user=follower)

        url = FOLLOWERS_URL.format(self.linghu.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # dongxie has followed users with even id
        response = self.dongxie_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            following = self.createUser('linghu_following{}'.format(i))
            friendship = self.createFriendship(from_user=self.linghu, to_user=following)
            friendships.append(friendship)
            if following.id % 2 == 0:
                self.createFriendship(from_user=self.dongxie, to_user=following)

        url = FOLLOWINGS_URL.format(self.linghu.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # dongxie has followed users with even id
        response = self.dongxie_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # linghu has followed all his following users
        response = self.linghu_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

        # test pull new friendships
        last_created_at = friendships[-1].created_at
        response = self.linghu_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        new_friends = [self.createUser('big_v{}'.format(i)) for i in range(3)]
        new_friendships = []
        for friend in new_friends:
            new_friendships.append(self.createFriendship(from_user=self.linghu, to_user=friend))
        response = self.linghu_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(len(response.data['results']), 3)
        for result, friendship in zip(response.data['results'], reversed(new_friendships)):
            self.assertEqual(result['created_at'], friendship.created_at)

    def _paginate_until_the_end(self, url, expect_pages, friendships):
        results, pages = [], 0
        response = self.anonymous_client.get(url)
        results.extend(response.data['results'])
        pages += 1
        while response.data['has_next_page']:
            self.assertEqual(response.status_code, 200)
            last_item = response.data['results'][-1]
            response = self.anonymous_client.get(url, {
                'created_at__lt': last_item['created_at'],
            })
            results.extend(response.data['results'])
            pages += 1

        self.assertEqual(len(results), len(friendships))
        self.assertEqual(pages, expect_pages)
        # friendship is in ascending order, results is in descending order
        for result, friendship in zip(results, friendships[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)

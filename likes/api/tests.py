from rest_framework.test import APIClient
from testing.testcases import TestCase


LIKE_BASE_URL = '/api/likes/'
TWEET_BASE_URL = '/api/tweets/'


class LikeApiTests(TestCase):

    def setUp(self):
        super(LikeApiTests, self).setUp()
        self.linghu, self.linghu_client = self.createUserAndClient('linghu')
        self.dongxie, self.dongxie_client = self.createUserAndClient('dongxie')

    def test_tweet_likes(self):
        tweet = self.createTweet(self.linghu)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.linghu_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # post success
        response = self.linghu_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)
        # 重复喜欢，不重复创建
        self.linghu_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.dongxie_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

        # 获取 tweet 内容时，喜欢的人按照时间倒序排列
        url = '{}{}/'.format(TWEET_BASE_URL, tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['likes_count'], 2)
        likes = response.data['likes']
        self.assertEqual(likes[0]['user']['id'], self.dongxie.id)
        self.assertEqual(likes[1]['user']['id'], self.linghu.id)

    def test_comment_likes(self):
        tweet = self.createTweet(self.linghu)
        comment = self.createComment(self.dongxie, tweet)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.linghu_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # 错误的 content_type
        response = self.linghu_client.post(LIKE_BASE_URL, {
            'content_type': 'coment',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)

        # 错误的 object_id
        response = self.linghu_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)

        # post success
        response = self.linghu_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)
        # 可以重复点喜欢，但不重复创建喜欢
        response = self.linghu_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)
        self.dongxie_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)

        url = '{}{}/'.format(TWEET_BASE_URL, tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['likes_count'], 2)

    def test_destroy(self):
        tweet = self.createTweet(self.linghu)
        comment = self.createComment(self.dongxie, tweet)
        like_comment_data = {'content_type': 'comment', 'object_id': comment.id}
        like_tweet_data = {'content_type': 'tweet', 'object_id': tweet.id}
        self.linghu_client.post(LIKE_BASE_URL, like_comment_data)
        self.dongxie_client.post(LIKE_BASE_URL, like_tweet_data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        cancel_url = LIKE_BASE_URL + 'cancel/'

        # 必须是登录用户
        response = self.anonymous_client.post(cancel_url, like_comment_data)
        self.assertEqual(response.status_code, 403)

        # get 不被允许
        response = self.linghu_client.get(cancel_url, like_comment_data)
        self.assertEqual(response.status_code, 405)

        # 找不到 content_type
        response = self.linghu_client.post(cancel_url, {
            'content_type': 'wrong',
            'object_id': 1,
        })
        self.assertEqual(response.status_code, 400)

        # 找不到 content_type
        response = self.linghu_client.post(cancel_url, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)

        # dongxie 没有点赞过评论，静默处理
        response = self.dongxie_client.post(cancel_url, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)
        # linghu 的点赞被取消
        response = self.linghu_client.post(cancel_url, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # linghu 没有点赞过推文，静默处理
        response = self.linghu_client.post(cancel_url, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)
        # dongxie 的点赞被取消
        response = self.dongxie_client.post(cancel_url, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 0)

    def test_tweet_likes_cache(self):
        tweet = self.createTweet(self.linghu)
        self.createNewsFeed(self.linghu, tweet)
        self.createNewsFeed(self.dongxie, tweet)

        data = {'content_type': 'tweet', 'object_id': tweet.id}
        tweet_url = '{}{}/'.format(TWEET_BASE_URL, tweet.id)
        for i in range(3):
            _, client = self.createUserAndClient('someone{}'.format(i))
            client.post(LIKE_BASE_URL, data)
            # check tweet api
            response = client.get(tweet_url)
            self.assertEqual(response.data['likes_count'], i + 1)
            tweet.refresh_from_db()
            self.assertEqual(tweet.likes_count, i + 1)

        self.dongxie_client.post(LIKE_BASE_URL, data)
        response = self.dongxie_client.get(tweet_url)
        self.assertEqual(response.data['likes_count'], 4)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 4)

        # check newsfeed api
        newsfeed_url = '/api/newsfeeds/'
        response = self.linghu_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['likes_count'], 4)
        response = self.dongxie_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['likes_count'], 4)

        # dongxie canceled likes
        self.dongxie_client.post(LIKE_BASE_URL + 'cancel/', data)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 3)
        response = self.dongxie_client.get(tweet_url)
        self.assertEqual(response.data['likes_count'], 3)
        response = self.linghu_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['likes_count'], 3)
        response = self.dongxie_client.get(newsfeed_url)
        self.assertEqual(response.data['results'][0]['tweet']['likes_count'], 3)

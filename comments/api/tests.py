from testing.testcases import TestCase
from rest_framework.test import APIClient
from comments.models import Comment
from django.utils import timezone


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):

    def setUp(self):
        super(CommentApiTests, self).setUp()
        self.linghu = self.createUser('linghu')
        self.linghu_client = APIClient()
        self.linghu_client.force_authenticate(self.linghu)
        self.dongxie = self.createUser('dongxie')
        self.dongxie_client = APIClient()
        self.dongxie_client.force_authenticate(self.dongxie)

        self.tweet = self.createTweet(self.linghu)

    def test_list(self):
        # 必须带 tweet_id
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # 带了 tweet_id 可以访问
        # 一开始没有评论
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # 评论按照时间顺序排序
        self.createComment(self.linghu, self.tweet, '1')
        self.createComment(self.dongxie, self.tweet, '2')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

    def test_create(self):
        # 匿名不可以创建
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # 啥参数都没带不行
        response = self.linghu_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)
        # 只带 tweet_id 不行
        response = self.linghu_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)
        # 只带 content 不行
        response = self.linghu_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        # tweet_id 和 content 都带才行
        response = self.linghu_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.linghu.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')

    def test_destroy(self):
        comment = self.createComment(self.linghu, self.tweet)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # 匿名不可以删除
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # 非本人不能删除
        response = self.dongxie_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # 本人可以删除
        count = Comment.objects.count()
        response = self.linghu_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.createComment(self.linghu, self.tweet, 'original')
        another_tweet = self.createTweet(self.dongxie)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # 使用 put 的情况下
        # 匿名不可以更新
        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        # 非本人不能更新
        response = self.dongxie_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')
        # 不能更新除 content 外的内容，静默处理，只更新内容
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.linghu_client.put(url, {
            'content': 'new',
            'user_id': self.dongxie.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.linghu)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_comments_count(self):
        tweet_url = '/api/tweets/{}/'.format(self.tweet.id)
        response = self.linghu_client.get(tweet_url)
        self.assertEqual(self.tweet.comments_count, 0)
        self.assertEqual(response.data['comments_count'], 0)

        data = {'tweet_id': self.tweet.id, 'content': 'a comment'}
        for i in range(2):
            _, client = self.createUserAndClient('user{}'.format(i))
            client.post(COMMENT_URL, data)
            response =client.get(tweet_url)
            self.assertEqual(response.data['comments_count'], i + 1)
            self.tweet.refresh_from_db()
            self.assertEqual(self.tweet.comments_count, i + 1)

        comment_data = self.dongxie_client.post(COMMENT_URL, data).data
        response = self.dongxie_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # update comment shouldn't update comments_count
        comment_url = '{}{}/'.format(COMMENT_URL, comment_data['id'])
        response = self.dongxie_client.put(comment_url, {'content': 'updated'})
        self.assertEqual(response.status_code, 200)
        response = self.dongxie_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # delete a comment will update comments_count
        response = self.dongxie_client.delete(comment_url)
        self.assertEqual(response.status_code, 200)
        response = self.linghu_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 2)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 2)

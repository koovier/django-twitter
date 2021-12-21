from django.utils import timezone
from testing.testcases import TestCase
from rest_framework.test import APIClient
from comments.models import Comment


COMMENT_URL = '/api/comments/'


class CommentApiTest(TestCase):

    def setUp(self):
        self.linghu = self.create_user('linghu')
        self.linghu_client = APIClient()
        self.linghu_client.force_authenticate(self.linghu)

        self.dongxie = self.create_user('dongxie')
        self.dongxie_client = APIClient()
        self.dongxie_client.force_authenticate(self.dongxie)

        self.tweet = self.create_tweet(self.linghu)

    def test_create(self):
        # 403 for post comment with anonymous user
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # 400 for no args
        response = self.linghu_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # 400 for missing content
        response = self.linghu_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # 400 for missing tweet id
        response = self.linghu_client.post(COMMENT_URL, {'content': 'test must fail'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual('tweet_id' in response.data['errors'], True)

        # 400 for comment exceed max length
        response = self.linghu_client.post(COMMENT_URL, {'tweet_id': self.tweet.id, 'content': '1' * 141, })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # 201 for successfully created
        response = self.linghu_client.post(COMMENT_URL, {'tweet_id': self.tweet.id, 'content': 'test succeeded!', })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.linghu.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], 'test succeeded!')

    def test_destroy(self):
        comment = self.create_comment(self.linghu, self.tweet)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        # 403 for delete comment with anonymous user
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # 400 for requester is not owner
        response = self.dongxie_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # 200 for successfully deleted
        count = Comment.objects.count()
        response = self.linghu_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_udpate(self):
        comment = self.create_comment(self.linghu, self.tweet, 'original')
        another_tweet = self.create_tweet(self.dongxie)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)

        response = self.dongxie_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')

        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        # user can only update content. Other requests will be ignored.
        response = self.linghu_client.put(url, {
            'content': 'New',
            'user_id': self.dongxie.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        # Pull latest data from database.
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'New')
        self.assertEqual(comment.user, self.linghu)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.updated_at, before_updated_at)
        self.assertNotEqual(comment.created_at, now)

    def test_list(self):
        # no tweet_id
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        response = self.anonymous_client.get(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        self.create_comment(self.linghu, self.tweet, '1')
        self.create_comment(self.dongxie, self.tweet, '2')
        self.create_comment(self.dongxie, self.create_tweet(self.dongxie), '3')
        response = self.anonymous_client.get(COMMENT_URL, {'tweet_id': self.tweet.id, })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        response = self.anonymous_client.get(COMMENT_URL, {'tweet_id': self.tweet.id, 'user_id': self.linghu.id})
        self.assertEqual(len(response.data['comments']), 2)

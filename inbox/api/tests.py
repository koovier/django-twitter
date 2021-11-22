from testing.testcases import TestCase

NOTIFICATION_BASE_URL = '/api/notifications/'
COMMENT_BASE_URL = '/api/comments/'
LIKE_BASE_URL = '/api/likes/'


class NotificationApiTests(TestCase):

    def setUp(self):
        super(NotificationApiTests, self).setUp()
        self.linghu, self.linghu_client = self.createUserAndClient('linghu')
        self.dongxie, self.dongxie_client = self.createUserAndClient('dongxie')
        self.linghu_tweet = self.createTweet(self.linghu)

    def test_comment_notifications(self):
        # 自己评论自己的 Tweet 不收到任何提醒
        response = self.linghu_client.post(COMMENT_BASE_URL, {
            'tweet_id': self.linghu_tweet.id,
            'content': 'self comment',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.linghu.notifications.count(), 0)
        self.assertEqual(self.dongxie.notifications.count(), 0)
        # 别人的评论会收到提醒
        response = self.dongxie_client.post(COMMENT_BASE_URL, {
            'tweet_id': self.linghu_tweet.id,
            'content': 'other comment',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.linghu.notifications.count(), 1)
        self.assertEqual(self.dongxie.notifications.count(), 0)

    def test_like_notifications(self):
        # 自己点赞自己的 Tweet 不收到任何提醒
        response = self.linghu_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': self.linghu_tweet.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.linghu.notifications.count(), 0)
        self.assertEqual(self.dongxie.notifications.count(), 0)
        # 别人的点赞会收到提醒
        response = self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': self.linghu_tweet.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.linghu.notifications.count(), 1)
        self.assertEqual(self.dongxie.notifications.count(), 0)

        # 点赞评论
        comment = self.createComment(self.linghu, self.linghu_tweet)
        response = self.linghu_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.linghu.notifications.count(), 1)
        self.assertEqual(self.dongxie.notifications.count(), 0)
        # 重复点赞不会收到重复提醒
        for i in range(2):
            response = self.dongxie_client.post(LIKE_BASE_URL, {
                'content_type': 'comment',
                'object_id': comment.id,
            })
            self.assertEqual(response.status_code, 201)
            self.assertEqual(self.linghu.notifications.count(), 2)
            self.assertEqual(self.dongxie.notifications.count(), 0)

    def test_unread_count(self):
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': self.linghu_tweet.id,
        })

        url = '/api/notifications/unread-count/'
        response = self.linghu_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.createComment(self.linghu, self.linghu_tweet)
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.linghu_client.get(url)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_all_as_read(self):
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': self.linghu_tweet.id,
        })
        comment = self.createComment(self.linghu, self.linghu_tweet)
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        unread_url = '/api/notifications/unread-count/'
        response = self.linghu_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'
        response = self.linghu_client.get(mark_url)
        self.assertEqual(response.status_code, 405)
        response = self.linghu_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.linghu_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_update(self):
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': self.linghu_tweet.id,
        })
        comment = self.createComment(self.linghu, self.linghu_tweet)
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.linghu.notifications.first()

        url = '/api/notifications/{}/'.format(notification.id)
        # post 不行，需要用 put
        response = self.dongxie_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)
        # 不可以被其他人改变 notification 状态
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)
        # 因为 queryset 是按照当前登陆用户来，所以会返回 404 而不是 403
        response = self.dongxie_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)
        # 成功标记为已读
        response = self.linghu_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        unread_url = '/api/notifications/unread-count/'
        response = self.linghu_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 1)

        # 再标记为未读
        response = self.linghu_client.put(url, {'unread': True})
        response = self.linghu_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)
        # 必须带 unread
        response = self.linghu_client.put(url, {'verb': 'newverb'})
        self.assertEqual(response.status_code, 400)
        # 不可修改其他的信息
        response = self.linghu_client.put(url, {'verb': 'newverb', 'unread': False})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'newverb')

    def test_list(self):
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': self.linghu_tweet.id,
        })
        comment = self.createComment(self.linghu, self.linghu_tweet)
        self.dongxie_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        # 匿名用户无法访问 api
        response = self.anonymous_client.get(NOTIFICATION_BASE_URL)
        self.assertEqual(response.status_code, 403)
        # dongxie 看不到任何 notifications
        response = self.dongxie_client.get(NOTIFICATION_BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # linghu 看到两个 notifications
        response = self.linghu_client.get(NOTIFICATION_BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        # 标记之后看到一个未读
        notification = self.linghu.notifications.first()
        notification.unread = False
        notification.save()
        response = self.linghu_client.get(NOTIFICATION_BASE_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.linghu_client.get(NOTIFICATION_BASE_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.linghu_client.get(NOTIFICATION_BASE_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)

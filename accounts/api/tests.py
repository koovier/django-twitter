from rest_framework.test import APIClient
from testing.testcases import TestCase

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@jiuzhang.com',
            password='correct password'
        )


    def test_login(self):
        # test case name must start with 'test_'
        # 400 for using get method
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 405)

        # 400 for wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password'
        })
        self.assertEqual(response.status_code, 400)

        # verify status is not  logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # 200 log in with correct info
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@jiuzhang.com')

        # verify status is logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # log in before test start
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password'
        })

        # verify user logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # 405 for using wrong method : get
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # 200 for use post method to successfully logout
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # verify status is logged out
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        }

        # 405 for using get method
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # 400 for using an invalid email for 400
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'wrong email format',
            'password': 'correct password',
        })
        print(response.data)
        self.assertEqual(response.status_code, 400)

        # 400 for password too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': '12345',
        })
        print(response.data)
        self.assertEqual(response.status_code, 400)

        # 400 for username too long
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is too long this string is over twenty characters long',
            'email': 'someone@jiuzhang.com',
            'password': 'correct password',
        })
        print(response.data)
        self.assertEqual(response.status_code, 400)

        # 200 for successfully sign up
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        # verify status is logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)





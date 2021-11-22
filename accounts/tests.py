from accounts.models import UserProfile
from testing.testcases import TestCase


class UserProfileTests(TestCase):

    def test_profile_property(self):
        linghu = self.createUser('linghu')
        self.assertEqual(UserProfile.objects.count(), 0)
        p = linghu.profile
        self.assertEqual(UserProfile.objects.count(), 1)

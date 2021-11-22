from testing.testcases import TestCase
from photos.models import Photo
from photos.constants import PhotoStatus


class PhotoTests(TestCase):

    def test_create_photo(self):
        # 测试可以成功创建 photo 的数据对象
        linghu = self.createUser('linghu')
        photo = Photo.objects.create(user=linghu)
        self.assertEqual(photo.user, linghu)
        self.assertEqual(photo.status, PhotoStatus.PENDING)

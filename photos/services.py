from photos.models import Photo


class PhotoService(object):

    @classmethod
    def create_photos_from_files(cls, user, files):
        # 也可以使用 bulk_create 来加速，不过因为瓶颈主要在图片上传
        # 所以 bulk_create，就没有比 for 循环创建有多好了
        photos = []
        for file in files:
            photo = Photo.objects.create(user=user, file=file)
            photos.append(photo)
        return photos

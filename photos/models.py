from django.db import models
from django.contrib.auth.models import User
from photos.constants import PhotoStatus, PHOTO_STATUS_CHOICES


class Photo(models.Model):
    status = models.IntegerField(
        default=PhotoStatus.PENDING,
        choices=PHOTO_STATUS_CHOICES,
    )
    file = models.FileField()
    # 谁上传了这张图片，这个信息虽然可以从 tweet 中获取到，但是重复的记录在 Image 里可以在
    # 使用上带来很多遍历，比如某个人经常上传一些不合法的照片，那么这个人新上传的照片可以被标记
    # 为重点审查对象。或者我们需要封禁某个用户上传的所有照片的时候，就可以通过这个 model 快速
    # 进行筛选
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    # 软删除(soft delete)标记，当一个照片被删除的时候，首先会被标记为已经被删除，在一定时间之后
    # 才会被真正的删除。这样做的目的是，如果在 tweet 被删除的时候马上执行真删除的通常会花费一定的
    # 时间，影响效率。可以用异步任务在后台慢慢做真删除。
    has_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # 方便审核人员按照日期筛选图片
    created_at_date = models.DateField(auto_now_add=True)

    class Meta:
        index_together = (
            ('user', 'created_at'),
            ('created_at_date', 'has_deleted'),
            ('created_at_date', 'status'),
        )

    def __str__(self):
        return '{} uploaded an image at {}'.format(self.user, self.created_at)

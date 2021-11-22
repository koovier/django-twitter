from utils.memcached_helper import MemcachedHelper
from django.contrib.auth.models import User


class UserService:

    @classmethod
    def get_user_by_id(cls, user_id):
        return MemcachedHelper.get_object_through_cache(User, user_id)

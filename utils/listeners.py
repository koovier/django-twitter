def invalidate_object_cache(sender, instance, **kwargs):
    from utils.memcached_helper import MemcachedHelper
    MemcachedHelper.invalidate_cached_object(sender, instance.id)

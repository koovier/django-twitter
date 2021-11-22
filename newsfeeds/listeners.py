def push_newsfeed_to_cache(sender, instance, created, **kwargs):
    if not created:
        return

    from newsfeeds.services import NewsFeedService
    NewsFeedService.push_newsfeed_to_cache(instance)

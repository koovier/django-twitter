from dateutil import parser
from django.conf import settings
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from utils.time_constants import MAX_TIMESTAMP


class EndlessPagination(BasePagination):
    page_size = settings.ENDLESS_PAGINATION_PAGE_SIZE

    def __init__(self):
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

    def _do_paginate_cached_list(self, cached_list, request):
        if 'created_at__gt' in request.query_params:
            # 兼容 iso 格式和 int 格式的时间戳
            try:
                created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            except ValueError:
                created_at__gt = int(request.query_params['created_at__gt'])
            objects = []
            for obj in cached_list:
                if obj.created_at > created_at__gt:
                    objects.append(obj)
                else:
                    break
            self.has_next_page = False
            return objects

        index = 0
        if 'created_at__lt' in request.query_params:
            # 兼容 iso 格式和 int 格式的时间戳
            try:
                created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            except ValueError:
                created_at__lt = int(request.query_params['created_at__lt'])
            for index, obj in enumerate(cached_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                # 没找到任何满足条件的 objects, 返回空数组
                # 注意这个 else 对应的是 for，参见 python 的 for else 语法
                cached_list = []
        self.has_next_page = len(cached_list) > index + self.page_size
        return cached_list[index: index + self.page_size]

    def paginate_queryset(self, queryset, request, view=None):
        # 思考问题：使用 created_at 作为分页的区分，可能会因为两个 tweet 有同样的 created_at
        # 导致在翻页时漏掉一个的情况。比如第一页是 [10, 9, 8, 7, 6]  第二页是 [6, 5, 4, 3, 2]
        # 有两个帖子的创建时间是6，在翻第二页的时候寻找 < 6 的最后5个帖子，会找到[5,4,3,2,1]
        # 从而漏掉了一个创建时间是 6 的帖子。这种情况出现概率是否会高？是否需要解决？是否需要在研发初期去解决？

        if 'created_at__gt' in request.query_params:
            # created_at__gt 用于下拉刷新的时候加载最新的内容进来
            # 为了简便起见，下拉刷新不做翻页机制，直接加载所有更新的数据
            # 因为如果数据很久没有更新的话，不会采用下拉刷新的方式进行更新，而是重新加载最新的数据
            created_at__gt = request.query_params['created_at__gt']
            queryset = queryset.filter(created_at__gt=created_at__gt)
            self.has_next_page = False
            return queryset.order_by('-created_at')

        if 'created_at__lt' in request.query_params:
            # created_at__lt 用于向上滚屏（往下翻页）的时候加载下一页的数据
            # 寻找 id < created_at__lt 的 objects 里按照 id 倒序的前 page_size + 1 个 objects
            # 比如目前的id列表是 [10, 9, 8, 7 .. 1] 如果 created_at__lt=10, page_size = 2
            # 则应该返回 [9, 8, 7]，多返回一个 object 的原因是为了判断是否还有下一页
            # 从而减少一次空加载。
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)

        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def paginate_cached_list(self, cached_list, request):
        paginated_list = self._do_paginate_cached_list(cached_list, request)
        # 如果是上翻页，paginated_list 里是所有的最新的数据，直接返回
        if 'created_at__gt' in request.query_params:
            return paginated_list
        # 如果还有下一页，说明 cached_list 里的数据还没有取完，也直接返回
        if self.has_next_page:
            return paginated_list
        # 如果 cached_list 的长度不足最大限制，说明 cached_list 里已经是所有数据了
        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list
        # 如果进入这里，说明可能存在在数据库里没有 load 在 cache 里的数据，需要直接去数据库查询
        return None

    def paginate_hbase(self, hb_model, row_key_prefix, request):
        if 'created_at__gt' in request.query_params:
            # created_at__gt 用于下拉刷新的时候加载最新的内容进来
            # 为了简便起见，下拉刷新不做翻页机制，直接加载所有更新的数据
            # 因为如果数据很久没有更新的话，不会采用下拉刷新的方式进行更新，而是重新加载最新的数据
            created_at__gt = request.query_params['created_at__gt']
            start = (*row_key_prefix, created_at__gt)
            stop = (*row_key_prefix, MAX_TIMESTAMP)
            objects = hb_model.filter(start=start, stop=stop)
            if len(objects) and objects[0].created_at == int(created_at__gt):
                objects = objects[:0:-1]
            else:
                objects = objects[::-1]
            self.has_next_page = False
            return objects

        if 'created_at__lt' in request.query_params:
            # created_at__lt 用于向上滚屏（往下翻页）的时候加载下一页的数据
            # 寻找 timestamp < created_at__lt 的 objects 里按照 timestamp 倒序的前 page_size + 1 个 objects
            # 比如目前的 timestamp 列表是 [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] 如果 created_at__lt=5, page_size = 2
            # 则应该返回 [4, 3, 2]，多返回一个 object 的原因是为了判断是否还有下一页从而减少一次空加载。
            # 由于 hbase 只支持 <= 的查询而不支持 <, 因此我们还需要再多取一个 item 保证 < 的 item 有 page_size + 1 个
            created_at__lt = request.query_params['created_at__lt']
            start = (*row_key_prefix, created_at__lt)
            stop = (*row_key_prefix, None)
            objects = hb_model.filter(start=start, stop=stop, limit=self.page_size + 2, reverse=True)
            if len(objects) and objects[0].created_at == int(created_at__lt):
                objects = objects[1:]
            if len(objects) > self.page_size:
                self.has_next_page = True
                objects = objects[:-1]
            else:
                self.has_next_page = False
            return objects

        # 没有任何参数，默认加载最新的一页
        prefix = (*row_key_prefix, None)
        objects = hb_model.filter(prefix=prefix, limit=self.page_size + 1, reverse=True)
        if len(objects) > self.page_size:
            self.has_next_page = True
            objects = objects[:-1]
        else:
            self.has_next_page = False
        return objects

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        })

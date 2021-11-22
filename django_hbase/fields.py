class HBaseField:

    def __init__(self, field_type, reverse=False, auto_now_add=False, column_family=None):
        self.field_type = field_type
        self.reverse = reverse
        self.column_family = column_family
        self.auto_now_add = auto_now_add and self.field_type == 'timestamp'
        # <HOMEWORK>
        # 增加 is_required 属性，默认为 true 和 default 属性，默认 None。
        # 并在 HbaseModel 中做相应的处理，抛出相应的异常信息

from django.conf import settings
from django_hbase.client import HBaseClient
from django_hbase.fields import HBaseField

import time


class HBaseModel:

    class EmptyColumnError(Exception):
        pass

    class BadRowKeyError(Exception):
        pass

    class Meta:
        table_name = None
        row_key = ()

    @property
    def row_key(self):
        return self.serialize_row_key(self.__dict__, raise_error=True)

    @classmethod
    def get_field_hash(cls):
        field_hash = {}
        for field in cls.__dict__:
            field_obj = getattr(cls, field)
            if isinstance(field_obj, HBaseField):
                field_hash[field] = field_obj
        return field_hash

    def __init__(self, **kwargs):
        for key, field in self.get_field_hash().items():
            value = kwargs.get(key)
            if field.auto_now_add and value is None:
                value = int(time.time() * 1000000)
            setattr(self, key, value)

    @classmethod
    def init_from_row(cls, row_key, row_data):
        if not row_data:
            return None
        data = cls.deserialize_row_key(row_key)
        for column_key, column_value in row_data.items():
            # remove column family
            column_key = column_key.decode('utf-8')
            key = column_key[column_key.find(':') + 1:]
            data[key] = cls.deserialize_field(key, column_value)
        return cls(**data)

    @classmethod
    def get_table_name(cls):
        if settings.TESTING:
            return 'test_{}'.format(cls.Meta.table_name)
        return cls.Meta.table_name

    @classmethod
    def get_table(cls):
        conn = HBaseClient.get_connection()
        if not cls.Meta.table_name:
            raise NotImplementedError('Missing table_name in HBaseModel meta class')
        return conn.table(cls.get_table_name())

    @classmethod
    def serialize_row_key(cls, data, raise_error=False):
        """
        serialize dict to bytes (not str)
        {key1: val1} => b"val1"
        {key1: val1, key2: val2} => b"val1:val2"
        {key1: val1, key2: val2, key3: val3} => b"val1:val2:val3"
        """
        field_hash = cls.get_field_hash()
        values = []
        for key, field in field_hash.items():
            if field.column_family:
                continue
            value = data.get(key)
            if value is None:
                if raise_error:
                    raise cls.BadRowKeyError("{} is missing in row key".format(key))
                break
            value = cls.serialize_field(key, field, value)
            values.append(value)
        return bytes(':'.join(values), encoding='utf-8')

    @classmethod
    def serialize_row_data(cls, data):
        row_data = {}
        field_hash = cls.get_field_hash()
        for key, field in field_hash.items():
            if not field.column_family:
                continue
            column_key = '{}:{}'.format(field.column_family, key)
            column_value = data.get(key)
            if column_value is None:
                continue
            row_data[column_key] = cls.serialize_field(key, field, column_value)
        return row_data


    @classmethod
    def deserialize_row_key(cls, row_key):
        """
        "val1" => {'key1': val1, 'key2': None, 'key3': None}
        "val1:val2" => {'key1': val1, 'key2': val2, 'key3': None}
        "val1:val2:val3" => {'key1': val1, 'key2': val2, 'key3': val3}
        """
        data = {}
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')
        row_key = row_key + ':'
        for key in cls.Meta.row_key:
            index = row_key.find(':')
            if index == -1:
                break
            data[key] = cls.deserialize_field(key, row_key[:index])
            row_key = row_key[index + 1:]
        return data

    @classmethod
    def deserialize_field(cls, key, value):
        field = cls.get_field_hash()[key]
        if field.reverse:
            value = value[::-1]
        if field.field_type in ['int', 'timestamp']:
            return int(value)
        return value

    @classmethod
    def serialize_field(cls, key, field, value):
        value = str(value)
        if ':' in value:
            raise cls.BadRowKeyError("row key {} should not contains ':' -> {}".format(
                key,
                value,
            ))
        if field.field_type == 'int':
            # 因为排序规则是按照字典序排序，那么就可能出现 1 10 2 这样的排序
            # 解决的办法是固定 int 的位数为 16 位（8的倍数更容易利用空间），不足位补 0
            value = str(value)
            while len(value) < 16:
                value = '0' + value
        if field.reverse:
            value = value[::-1]
        return value

    @classmethod
    def drop_table(cls):
        if not settings.TESTING:
            raise Exception('You can not drop table outside of unit tests')
        conn = HBaseClient.get_connection()
        conn.delete_table(cls.get_table_name(), True)

    @classmethod
    def create_table(cls):
        conn = HBaseClient.get_connection()
        tables = [table.decode('utf-8') for table in conn.tables()]
        if cls.get_table_name() in tables:
            return
        column_families = {
            field.column_family: dict()
            for key, field in cls.get_field_hash().items()
            if field.column_family is not None
        }
        conn.create_table(cls.get_table_name(), column_families)

    @classmethod
    def serialize_row_key_from_tuple(cls, row_key_tuple):
        if row_key_tuple is None:
            return None
        data = {
            key: value
            for key, value in zip(cls.Meta.row_key, row_key_tuple)
        }
        return cls.serialize_row_key(data)

    def save(self, batch=None):
        row_data = self.serialize_row_data(self.__dict__)
        # 如果 row_data 为空，即没有任何 column key values 需要存储 hbase 会直接不存储
        # 这个 row_key, 因此我们可以 raise 一个 exception 提醒调用者，避免存储空值
        if len(row_data) == 0:
            raise self.EmptyColumnError()
        if batch:
            batch.put(self.row_key, row_data)
        else:
            table = self.get_table()
            table.put(self.row_key, row_data)

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        row = table.row(row_key)
        return cls.init_from_row(row_key, row)

    @classmethod
    def create(cls, batch=None, **kwargs):
        instance = cls(**kwargs)
        instance.save(batch=batch)
        return instance

    @classmethod
    def batch_create(cls, batch_data):
        table = cls.get_table()
        batch = table.batch()
        results = []
        for data in batch_data:
            results.append(cls.create(batch=batch, **data))
        batch.send()
        return results

    @classmethod
    def delete(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        return table.delete(row_key)

    # <HOMEWORK> 实现一个 get_or_create 的方法，返回 (instance, created)

    @classmethod
    def filter(cls, start=None, stop=None, prefix=None, limit=None, reverse=False):
        # serialize tuple to str
        row_start = cls.serialize_row_key_from_tuple(start)
        row_stop = cls.serialize_row_key_from_tuple(stop)
        row_prefix = cls.serialize_row_key_from_tuple(prefix)

        # scan table
        table = cls.get_table()
        rows = table.scan(row_start, row_stop, row_prefix, limit=limit, reverse=reverse)

        # deserialize to instance list
        results = []
        for row_key, row_data in rows:
            instance = cls.init_from_row(row_key, row_data)
            results.append(instance)
        return results

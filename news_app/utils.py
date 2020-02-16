from sqlalchemy.inspection import inspect


class Serializer(object):

    def serialize(self):
        return {attr: getattr(self, attr) for attr in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(obj_list):
        return [obj.serialize() for obj in obj_list]

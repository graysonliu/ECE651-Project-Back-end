from sqlalchemy.inspection import inspect


class Serializer(object):

    def serialize(self):
        return {attr: getattr(self, attr) for attr in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(obj_list, **kw):
        if not kw:
            return [obj.serialize() for obj in obj_list]
        else:
            s_list = []
            for obj in obj_list:
                for k, v in kw.items():
                    if getattr(obj, k) == v:
                        s_list.append(obj.serialize())
            return s_list

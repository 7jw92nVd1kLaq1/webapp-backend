from rest_framework.serializers import SerializerMetaclass, ModelSerializer
from rest_framework.fields import Field


class CustomerSerializerMetaClass(SerializerMetaclass):
    @classmethod
    def _get_declared_fields(cls, bases, attrs):
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, obj in list(attrs.items()) if isinstance(obj, Field)]
        fields.sort(key=lambda x: x[1]._creation_counter)

        for each in fields:
            if each == 'orders_as_customer':
                fields[each].fields.pop('customer')

        print(fields)

        # Ensures a base class field doesn't override cls attrs, and maintains
        # field precedence when inheriting multiple parents. e.g. if there is a
        # class C(A, B), and A and B both define 'field', use 'field' from A.
        known = set(attrs)

        def visit(name):
            known.add(name)
            return name

        base_fields = []
        for base in bases:
            print(f"base: {base}")
            if hasattr(base, '_declared_fields'):
                for name, f in base._declared_fields.items():
                    print(f"name, f: {name} {f}")
                    if name not in known:
                        base_fields.append((visit(name), f))

        return dict(base_fields + fields)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_fields'] = cls._get_declared_fields(bases, attrs)
        return super().__new__(cls, name, bases, attrs)

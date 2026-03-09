from enum import Enum
from typing import Any


def add_to_dict_if_not_none(data: dict, key: str, value: Any):
    if value is not None:
        data[key] = value


def format_value_for_graphql_string(value: Any):
    if isinstance(value, dict):
        return f"{{{dict_to_graphql_string(value)}}}"

    elif isinstance(value, bool):
        return f"{str(value).lower()}"

    elif isinstance(value, (list, set)):
        out = "["
        for list_item in value:
            if isinstance(list_item, dict):
                out += f"{{{dict_to_graphql_string(list_item)}}},"
            else:
                out += f"{format_value_for_graphql_string(list_item)}"
        out = out.rstrip(",")
        out += "]"
        return out

    elif isinstance(value, int):
        return f"{value}"

    elif isinstance(value, Enum):
        return f"{value.value}"

    else:
        return f'"{value}"'


def dict_to_graphql_string(data: dict):
    out = ""
    for key, value in data.items():
        out += f"{key}: {format_value_for_graphql_string(value)},"

    out = out.rstrip(",")
    return out


# extend the dict class so this is natively json serializable
class Field(dict):
    def __init__(self, name: str, arguments: dict = None, subfields: list = None):
        self.name = name
        if arguments is None:
            arguments = dict()
        if subfields is None:
            subfields = list()

        self.arguments = arguments
        self.subfields = subfields
        super().__init__(name=name, arguments=arguments, subfields=subfields)

    def __str__(self):
        out = f"{self.name}"
        if self.arguments:
            out += "("
            out += dict_to_graphql_string(self.arguments)
            out += ")"

        out += "{"
        for subfield in self.subfields:
            out += f"{subfield},"

        out = out.rstrip(",")
        out += "}"
        return out


# extend the dict class so this is natively json serializable
class GraphQLQuery(dict):
    def __init__(self, operation):
        self.operation = operation
        self.fields = list()
        super().__init__(operation=operation, fields=self.fields)

    def add_field(self, field: Field):
        self.fields.append(field)

    def to_gql_string(self):
        out = f"{self.operation}{{"
        for field in self.fields:
            out += f"{field}"
        out += "}"
        return out

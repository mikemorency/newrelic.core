import logging

from ansible_collections.newrelic.core.plugins.module_utils.nr_object_base import (
    NrObjectBase,
)


logger = logging.getLogger(__name__)


class Tag:
    def __init__(self, name: str, values: list):
        self.name = name
        if not isinstance(values, list):
            values = [values]
        self.values = {str(v) for v in values}

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False

        return self.name == other.name and self.values == other.values

    def __repr__(self):
        return str({self.name: self.values})


class EntityTags:
    def __init__(self, tag_data: dict = None):
        self.tags = dict()
        if not tag_data:
            tag_data = dict()

        for data_key, data_value in tag_data.items():
            self.tags[data_key] = Tag(name=data_key, values=data_value)

    def __iter__(self):
        yield from self.tags.values()

    def __repr__(self):
        return str({key: tag.values for key, tag in self.tags.items()})

    def __len__(self):
        return len(self.tags)

    def __eq__(self, other):
        if not isinstance(other, EntityTags):
            return False

        return self.tags == other.tags

    def merge(self, other):
        o = EntityTags()
        o.tags = {**self.tags, **other.tags}
        return o

    def contains_tag(self, tag):
        if tag.name not in self.tags:
            return False

        return self.tags[tag.name].values.issuperset(tag.values)

    def to_json(self):
        return {tag.name: list(tag.values) for tag in self.tags.values()}

    def remove_key(self, key: str):
        if key in self.tags:
            removed = self.tags[key]
            del self.tags[key]
            return removed

    def remove_values(self, tag):
        if tag.name not in self.tags:
            return
        new_tag = self.tags[tag.name]
        if not new_tag.values.union(tag.values):
            return

        overlap = new_tag.values.intersection(tag.values)
        new_tag.values = new_tag.values - tag.values
        self.tags[tag.name] = new_tag
        return Tag(name=new_tag.name, values=list(overlap))

    def add_tag(self, tag):
        if tag.name not in self.tags:
            self.tags[tag.name] = tag
            return tag
        new_tag = self.tags[tag.name]
        logger.debug("Add tag %s to tag %s", tag, new_tag)
        if new_tag == tag or new_tag.values.issuperset(tag.values):
            return

        missing = tag.values - new_tag.values
        new_tag.values = new_tag.values.union(tag.values)
        self.tags[tag.name] = new_tag
        return Tag(name=tag.name, values=list(missing))

    def replace_tag(self, tag):
        if tag.name not in self.tags:
            self.tags[tag.name] = tag
            return tag

        if self.tags[tag.name] == tag:
            return

        self.tags[tag.name] = tag
        return tag


class Entity(NrObjectBase):
    def __init__(self, name: str, account_id: str, guid: str = None):
        super().__init__(name=name, account_id=account_id)
        self.guid = guid
        self.tags = dict()
        self._equality_attrs.update(["tags"])

    @classmethod
    def from_api_data(cls, data):
        obj = cls(
            name=data["name"],
            account_id=data["accountId"],
            guid=data["guid"],
        )
        obj.tags = EntityTags(tag_data={t["key"]: t["values"] for t in data["tags"]})
        obj.type = data["type"]

        return obj

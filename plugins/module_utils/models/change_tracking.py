import logging

from ansible_collections.newrelic.core.plugins.module_utils.models.nr_object_base import (
    NrObjectBase,
)


logger = logging.getLogger(__name__)


class ChangeTrackingEventBase(NrObjectBase):
    def __init__(self):
        super().__init__(name="", account_id="")
        self._equality_attrs = set()


class DeploymentEvent(ChangeTrackingEventBase):
    def __init__(
        self, entity_guid: str, version: str, id: str = None, timestamp: int = None
    ):
        super().__init__()
        self.entity_guid = entity_guid
        self.version = version
        self.id = id
        self.timestamp = timestamp

        self.changelog = None
        self.commit = None
        self.deep_link = None
        self.deployment_type = None
        self.description = None
        self.group_id = None
        self.user = None
        self._equality_attrs.update(
            [
                "entity_guid",
                "version",
                "id",
                "changelog",
                "commit",
                "deep_link",
                "deployment_type",
                "description",
                "group_id",
                "user",
            ]
        )
        if self.timestamp is not None:
            self._equality_attrs.update(["timestamp"])

    @classmethod
    def from_api_data(cls, data):
        obj = cls(
            entity_guid=data["entityGuid"],
            version=data["groupId"],
            id=data["incidentPreference"],
            timestamp=data["timestamp"],
        )
        obj.changelog = data.get("changelog")
        obj.commit = data.get("commit")
        obj.deep_link = data.get("deepLink")
        obj.deployment_type = data.get("deploymentType")
        obj.description = data.get("description")
        obj.group_id = data.get("groupId")
        obj.user = data.get("user")

        return obj

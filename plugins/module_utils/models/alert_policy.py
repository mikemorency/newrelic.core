from enum import Enum
import logging

from ansible_collections.newrelic.core.plugins.module_utils.models.nr_object_base import (
    NrObjectBase,
    NrStringEnum
)


logger = logging.getLogger(__name__)


class IncidentPreference(NrStringEnum):
    PER_POLICY = "PER_POLICY"
    PER_CONDITION = "PER_CONDITION"
    PER_CONDITION_AND_TARGET = "PER_CONDITION_AND_TARGET"


class AlertPolicy(NrObjectBase):
    def __init__(
        self,
        name: str,
        incident_preference: IncidentPreference,
        account_id: str,
        id: str = None,
    ):
        super().__init__(name=name, account_id=account_id)
        self.id = id
        self.incident_preference = incident_preference
        self._equality_attrs.update(["incident_preference"])

    @classmethod
    def from_api_data(cls, data):
        obj = cls(
            name=data["name"],
            account_id=data["accountId"],
            incident_preference=IncidentPreference[data["incidentPreference"]],
            id=data["id"],
        )

        return obj

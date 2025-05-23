import logging

from ansible_collections.newrelic.core.plugins.module_utils.alert_policy.query_templates import (
    AlertPolicyTemplates,
)
from ansible_collections.newrelic.core.plugins.module_utils.nr_object_base import (
    NrObjectBase,
)


logger = logging.getLogger(__name__)


class AlertPolicy(NrObjectBase):
    J2_SEARCH_QUERY = AlertPolicyTemplates.j2_get_from_search()
    J2_DELETE_QUERY = AlertPolicyTemplates.j2_delete()
    J2_CREATE_QUERY = AlertPolicyTemplates.j2_create()
    J2_UPDATE_QUERY = AlertPolicyTemplates.j2_update()

    def __init__(
        self,
        name: str,
        incident_preference: str,
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
            incident_preference=data["incidentPreference"],
            id=data["id"],
        )

        return obj

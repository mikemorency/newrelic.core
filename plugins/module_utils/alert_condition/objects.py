import logging

from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.query_templates import (
    NrqlBaseClassAlertConditionTemplates,
    NrqlStaticAlertConditionTemplates,
)
from ansible_collections.newrelic.core.plugins.module_utils.entity.objects import (
    Entity,
)


logger = logging.getLogger(__name__)


class IncidentTerm:
    def __init__(
        self,
        threshold: int,
        priority: str,
        operator: str,
        duration: int,
        occurrences: str,
    ):
        self.threshold = int(threshold)
        self.priority = priority
        self.operator = operator
        self.duration = int(duration)
        self.occurrences = occurrences

    @classmethod
    def from_api_data(cls, data):
        obj = cls(
            threshold=data["threshold"],
            priority=data["priority"],
            operator=data["operator"],
            duration=data["thresholdDuration"],
            occurrences=data.get("thresholdOccurrences"),
        )

        return obj

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, new_val):
        if new_val not in ["WARNING", "CRITICAL"]:
            raise Exception(
                "Priority must be either WARNING or CRITICAL, got %s" % new_val
            )
        self._priority = new_val

    def to_json(self):
        return self.__dict__


class NrqlAlertConditionBase(Entity):
    J2_SEARCH_QUERY = NrqlBaseClassAlertConditionTemplates.j2_get_from_search()
    J2_DELETE_QUERY = NrqlBaseClassAlertConditionTemplates.j2_delete()

    def __init__(
        self,
        name: str,
        account_id: str,
        policy_id: str = None,
        id: str = None,
        guid: str = None,
    ):
        super().__init__(name=name, account_id=account_id, guid=guid)
        self.id = id
        self.entity_type = None
        self.enabled = False
        self.description = ""
        self.policy_id = policy_id
        self.incident_terms = []
        self._equality_attrs.update(
            ["entity_type", "description", "policy_id", "incident_terms"]
        )

    @classmethod
    def from_api_data(cls, data, account_id):
        if data["type"] == "STATIC":
            return NrqlStaticAlertCondition.from_api_data(
                data=data, account_id=account_id
            )

        raise Exception("Unknown type, can't create ob from data: %s" % data["type"])

    def output_identity_dict(self):
        return {"name": self.name, "id": self.id, "guid": self.guid}


class NrqlStaticAlertCondition(NrqlAlertConditionBase):
    J2_CREATE_QUERY = NrqlStaticAlertConditionTemplates.j2_create()
    J2_UPDATE_QUERY = NrqlStaticAlertConditionTemplates.j2_update()

    def __init__(self, name: str, account_id: str, policy_id: str, id: str = None):
        super().__init__(name=name, account_id=account_id, policy_id=policy_id, id=id)
        self.entity_type = "STATIC"
        self.nrql_query = ""
        self.runbook_url = None
        self.description = None

        self.data_aggregation_window = None
        self.data_aggregation_method = None
        self.data_aggregation_timer = None
        self.data_aggregation_delay = None
        self.data_slide_by = None

        self._equality_attrs.update(
            [
                "runbook_url",
                "nrql_query",
                "data_aggregation_window",
                "data_aggregation_method",
                "data_aggregation_timer",
                "data_aggregation_delay",
                "data_slide_by",
                "evaluation_delay",
            ]
        )

    def validate_properties(self):
        if (
            self.data_aggregation_method == "EVENT_FLOW"
            and self.data_aggregation_window
        ):
            for term in self.incident_terms:
                if term.duration % self.data_aggregation_window != 0:
                    raise ValueError(
                        "Incident duration must be a multiple of data_aggregation_window "
                        "when using EVENT_FLOW"
                    )

    @classmethod
    def from_api_data(cls, data, account_id):
        obj = cls(
            data["name"],
            account_id=account_id,
            policy_id=data["policyId"],
            id=data["id"],
        )

        obj.enabled = data.get("enabled")
        obj.guid = data.get("entityGuid")
        obj.nrql_query = data.get("nrql")["query"]
        obj.description = data.get("description")
        obj.runbook_url = data.get("runbookUrl")
        obj.data_aggregation_window = data.get("signal")["aggregationWindow"]
        obj.data_aggregation_method = data.get("signal")["aggregationMethod"]
        obj.data_aggregation_timer = data.get("signal")["aggregationTimer"]
        obj.data_aggregation_delay = data.get("signal")["aggregationDelay"]
        obj.data_slide_by = data.get("signal")["slideBy"]
        obj.evaluation_delay = data.get("signal")["evaluationDelay"]
        for term in data.get("terms", []):
            obj.incident_terms.append(IncidentTerm.from_api_data(term))

        return obj

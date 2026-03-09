import logging

from ansible_collections.newrelic.core.plugins.module_utils.models.entity import (
    Entity,
)
from ansible_collections.newrelic.core.plugins.module_utils.models.nr_object_base import (
    NrStringEnum,
)

logger = logging.getLogger(__name__)


class IncidentPriority(NrStringEnum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


class IncidentOperator(NrStringEnum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    ABOVE_OR_EQUALS = "ABOVE_OR_EQUALS"
    BELOW_OR_EQUALS = "BELOW_OR_EQUALS"
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"


class IncidentOccurences(NrStringEnum):
    AT_LEAST_ONCE = "AT_LEAST_ONCE"
    ALL = "ALL"


class DataAggregationMethod(NrStringEnum):
    EVENT_TIMER = "EVENT_TIMER"
    EVENT_FLOW = "EVENT_FLOW"
    CADENCE = "CADENCE"


class IncidentTerm:
    def __init__(
        self,
        threshold: int,
        priority: IncidentPriority,
        operator: IncidentOperator,
        duration: int,
        occurrences: IncidentOccurences,
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
            priority=IncidentPriority[data["priority"]],
            operator=IncidentOperator[data["operator"]],
            duration=data["thresholdDuration"],
            occurrences=IncidentOccurences[data.get("thresholdOccurrences")],
        )

        return obj

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def to_json(self):
        return self.__dict__


class NrqlAlertConditionBase(Entity):
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
        self.evaluation_delay = None

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
            self.data_aggregation_method is DataAggregationMethod.EVENT_FLOW
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
        obj.data_aggregation_method = DataAggregationMethod[
            data.get("signal")["aggregationMethod"]
        ]
        obj.data_aggregation_timer = data.get("signal")["aggregationTimer"]
        obj.data_aggregation_delay = data.get("signal")["aggregationDelay"]
        obj.data_slide_by = data.get("signal")["slideBy"]
        obj.evaluation_delay = data.get("signal")["evaluationDelay"]
        for term in data.get("terms", []):
            obj.incident_terms.append(IncidentTerm.from_api_data(term))

        return obj

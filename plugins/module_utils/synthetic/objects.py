import logging

from ansible_collections.newrelic.core.plugins.module_utils.entity.objects import (
    Entity,
)
from ansible_collections.newrelic.core.plugins.module_utils.synthetic.query_templates import (
    SyntheticMonitorBaseClassTemplates,
    PingSyntheticMonitorTemplates,
)


logger = logging.getLogger(__name__)


class SyntheticMonitorBase(Entity):
    J2_SEARCH_QUERY = SyntheticMonitorBaseClassTemplates.j2_get_from_search()
    J2_DELETE_QUERY = SyntheticMonitorBaseClassTemplates.j2_delete()
    PUBLIC_LOCATION_NAMES_TO_IDS = {
        "San Francisco, CA, USA": "AWS_US_WEST_1",
        "Washington, DC, USA": "AWS_US_EAST_1",
        "Columbus, OH, USA": "AWS_US_EAST_2",
    }

    def __init__(self, name: str, account_id: str, id: str = None, guid: str = None):
        super().__init__(name=name, account_id=account_id, guid=guid)
        self._equality_attrs.update(
            [
                "entity_type",
                "url",
                "period",
                "public_locations",
                "private_locations",
                "enabled",
                "verify_ssl",
                "monitor_type",
                # validation string cannot be checked on existing monitors, so it is null
                # unless explicitly set
                "validation_string",
            ]
        )
        self.entity_type = "MONITOR"
        self.monitor_type = None
        self.url = ""
        self.period = ""
        self.id = id
        self.public_locations = []
        self.private_locations = []
        self.enabled = False
        self.validation_string = None
        self.verify_ssl = False

    @staticmethod
    def period_value_to_id(period):
        try:
            p = int(period)
        except ValueError:
            raise Exception(
                "Period value should be an int when converting to ID. Got %s" % period
            )

        if p == 1:
            return "EVERY_MINUTE"
        if p < 60:
            return "EVERY_%s_MINUTES" % p
        if p == 60:
            return "EVERY_HOUR"
        if p == 1440:
            return "EVERY_DAY"

        return "EVERY_%s_HOURS" % int(p / 60)

    @classmethod
    def from_api_data(cls, data):
        obj = cls(data["name"], account_id=data["accountId"])

        obj.enabled = True if data["monitorSummary"]["status"] == "ENABLED" else False
        obj.id = data["monitorId"]
        obj.guid = data["guid"]
        obj.url = data["monitoredUrl"]
        logger.debug(
            "Creating monitor from api data and got period of %s", data["period"]
        )
        obj.period = SyntheticMonitorBase.period_value_to_id(data["period"])

        for tag in data["tags"]:
            if tag["key"] == "privateLocation":
                obj.private_locations = {tag["values"]}
                continue
            if tag["key"] == "publicLocation":
                obj.public_locations = [
                    obj.PUBLIC_LOCATION_NAMES_TO_IDS[value] for value in tag["values"]
                ]
                continue
            if tag["key"] == "useTlsValidation":
                obj.verify_ssl = True if tag["values"][0].lower() == "true" else False
                continue
            if tag["key"] == "responseValidationText":
                obj.validation_string = tag["values"][0]
                continue

        return obj

    def __eq__(self, other):
        if not isinstance(other, SyntheticMonitorBase):
            return False

        for attr in self._equality_attrs:
            if attr in ("public_locations", "private_locations"):
                if set(getattr(self, attr)) == set(getattr(other, attr)):
                    continue
            if getattr(self, attr) == getattr(other, attr):
                continue

            logger.debug(
                "%s   -   %s != %s", attr, getattr(self, attr), getattr(other, attr)
            )
            return False

        return True


class PingSyntheticMonitor(SyntheticMonitorBase):
    MONITOR_TYPE = "SIMPLE"
    J2_CREATE_QUERY = PingSyntheticMonitorTemplates.j2_create()
    J2_UPDATE_QUERY = PingSyntheticMonitorTemplates.j2_update()

    def __init__(self, name: str, account_id: str):
        super().__init__(name, account_id)
        self.monitor_type = PingSyntheticMonitor.MONITOR_TYPE

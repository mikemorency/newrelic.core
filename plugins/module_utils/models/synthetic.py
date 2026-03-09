import logging

from ansible_collections.newrelic.core.plugins.module_utils.models.entity import (
    Entity,
)
from ansible_collections.newrelic.core.plugins.module_utils.models.nr_object_base import (
    NrStringEnum,
)


logger = logging.getLogger(__name__)


class MonitorPeriod(NrStringEnum):
    EVERY_MINUTE = "EVERY_MINUTE"
    EVERY_5_MINUTES = "EVERY_5_MINUTES"
    EVERY_10_MINUTES = "EVERY_10_MINUTES"
    EVERY_15_MINUTES = "EVERY_15_MINUTES"
    EVERY_30_MINUTES = "EVERY_30_MINUTES"
    EVERY_HOUR = "EVERY_HOUR"
    EVERY_6_HOURS = "EVERY_6_HOURS"
    EVERY_12_HOURS = "EVERY_12_HOURS"
    EVERY_DAY = "EVERY_DAY"

    @classmethod
    def from_minutes(cls, minutes):
        try:
            p = int(minutes)
        except ValueError:
            raise Exception(
                "Minutes value should be an int when converting to MonitorPeriod. Got %s"
                % minutes
            )

        if p == 1:
            return MonitorPeriod.EVERY_MINUTE
        if p < 60:
            return MonitorPeriod["EVERY_%s_MINUTES" % p]
        if p == 60:
            return MonitorPeriod.EVERY_HOUR
        if p == 1440:
            return MonitorPeriod.EVERY_DAY

        return MonitorPeriod["EVERY_%s_HOURS" % int(p / 60)]


class SyntheticMonitorBase(Entity):
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
                "monitor_type",
                # validation string cannot be checked on existing monitors, so it is null
                # unless explicitly set
            ]
        )
        self.entity_type = "MONITOR"
        self.monitor_type = None
        self.url = ""
        self.period = None
        self.id = id
        self.public_locations = []
        self.private_locations = []
        self.enabled = False

    @classmethod
    def from_api_data(cls, data):
        monitor_type = data["monitorType"]
        if monitor_type == PingSyntheticMonitor.MONITOR_TYPE:
            return PingSyntheticMonitor.from_api_data(data)
        elif monitor_type == CertSyntheticMonitor.MONITOR_TYPE:
            return CertSyntheticMonitor.from_api_data(data)

        raise Exception("Unknown monitor type %s" % monitor_type)

    def _from_api_data_common(self, data):
        self.enabled = True if data["monitorSummary"]["status"] == "ENABLED" else False
        self.id = data["monitorId"]
        self.guid = data["guid"]
        self.url = data["monitoredUrl"]
        logger.debug(
            "Creating monitor from api data and got period of %s", data["period"]
        )
        self.period = MonitorPeriod.from_minutes(data["period"])

        for tag in data["tags"]:
            if tag["key"] == "privateLocation":
                self.private_locations = {tag["values"]}
                continue
            if tag["key"] == "publicLocation":
                self.public_locations = [
                    self.PUBLIC_LOCATION_NAMES_TO_IDS[value] for value in tag["values"]
                ]
                continue

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

    def __init__(self, name: str, account_id: str):
        super().__init__(name, account_id)
        self.monitor_type = PingSyntheticMonitor.MONITOR_TYPE
        self.validation_string = None
        self.verify_ssl = False
        self._equality_attrs.update(["verify_ssl", "validation_string"])

    @classmethod
    def from_api_data(cls, data):
        obj = cls(data["name"], account_id=data["accountId"])
        obj._from_api_data_common(data)

        for tag in data["tags"]:
            if tag["key"] == "useTlsValidation":
                obj.verify_ssl = True if tag["values"][0].lower() == "true" else False
                continue
            if tag["key"] == "responseValidationText":
                obj.validation_string = tag["values"][0]
                continue

        return obj


class CertSyntheticMonitor(SyntheticMonitorBase):
    MONITOR_TYPE = "CERT_CHECK"

    def __init__(self, name: str, account_id: str):
        super().__init__(name, account_id)
        self.monitor_type = CertSyntheticMonitor.MONITOR_TYPE
        self.days_before_cert_expires_to_trigger_failure = None
        self._equality_attrs.update(["days_before_cert_expires_to_trigger_failure"])

    @classmethod
    def from_api_data(cls, data):
        obj = cls(data["name"], account_id=data["accountId"])
        obj._from_api_data_common(data)

        for tag in data["tags"]:
            if tag["key"] == "daysUntilExpiration":
                obj.days_before_cert_expires_to_trigger_failure = int(tag["values"][0])
                break  # break since this is the only tag we need

        return obj

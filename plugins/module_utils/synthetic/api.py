import logging
import time

from ansible_collections.newrelic.core.plugins.module_utils.synthetic.objects import (
    SyntheticMonitorBase,
    PingSyntheticMonitor,
)
from ansible_collections.newrelic.core.plugins.module_utils.nerdgraph_api_base import (
    NerdGraphApiBase,
)


logger = logging.getLogger(__name__)


class SyntheticMonitorQueryError(Exception):
    def __init__(self, error_descriptions, monitor, action):
        self.monitor = monitor
        self.error_descriptions = error_descriptions
        self.action = action
        super().__init__(
            "Failed to %s monitor %s because %s"
            % (action, monitor.name, error_descriptions)
        )


class SyntheticMonitorApi(NerdGraphApiBase):
    def __init__(
        self,
        api_key: str,
        wait_for_propegation: bool = True,
        propegation_timeout: int = 10,
    ):
        super().__init__(
            api_key=api_key,
            wait_for_propegation=wait_for_propegation,
            propegation_timeout=propegation_timeout,
        )

    def get_monitor_by_name_and_account(self, name, account_id):
        existing_monitors, _ = (  # pylint: disable=disallowed-name
            self.get_monitors_from_query(
                entity_search_query="domain = 'SYNTH' AND type = 'MONITOR' AND name = '%s'"
                % name,
                account_id=account_id,
            )
        )

        if len(existing_monitors) == 1:
            return existing_monitors[0]
        elif not existing_monitors:
            return None
        else:
            raise Exception("Multiple synthetic monitors matched name query....")

    def get_monitors_from_query(
        self, entity_search_query: str, account_id: str, cursor: str = ""
    ) -> list:
        logger.info("Getting monitors from search '%s'", entity_search_query)
        query_template = self.jinja_env.from_string(
            SyntheticMonitorBase.J2_SEARCH_QUERY
        )
        query = query_template.render(
            entity_search_query=entity_search_query,
            account_id=account_id,
            cursor=cursor,
        )
        r = self.run_query(query=query)
        try:
            query_monitors = r["data"]["actor"]["entitySearch"]["results"]["entities"]
            next_cursor = r["data"]["actor"]["entitySearch"]["results"]["nextCursor"]
        except KeyError as e:
            logger.fatal("Encountered key error on '%s'", e)
            logger.fatal("response=%s", r)
            raise Exception("Query response did not match excepted format")

        logger.info(
            "Found %s monitors. Next cursor is %s", len(query_monitors), next_cursor
        )
        found_monitors = []
        for monitor_data in query_monitors:
            found_monitors += [self.__create_monitor_from_data(monitor_data)]
        return found_monitors, next_cursor

    def __create_monitor_from_data(self, monitor_data):
        if monitor_data["monitorType"] == PingSyntheticMonitor.MONITOR_TYPE:
            return PingSyntheticMonitor.from_api_data(monitor_data)

        raise Exception("Unknown monitor type %s" % monitor_data["monitorType"])

    def delete_monitor(self, monitor: SyntheticMonitorBase) -> str:
        logger.info(
            "Deleting synthetic monitor %s with GUID %s", monitor.name, monitor.guid
        )
        query_template = self.jinja_env.from_string(monitor.J2_DELETE_QUERY)
        query = query_template.render(monitor=monitor)
        r = self.run_query(query=query)
        self.__wait_for_monitor_to_not_exist(monitor=monitor)
        return r["data"]["syntheticsDeleteMonitor"]["deletedGuid"]

    def create_monitor(self, monitor: SyntheticMonitorBase):
        logger.info("Creating synthetic monitor %s", monitor.name)
        query_template = self.jinja_env.from_string(monitor.J2_CREATE_QUERY)
        query = query_template.render(monitor=monitor)
        r = self.run_query(query=query)
        logger.debug(r)
        self.raise_for_errors(
            r["data"]["syntheticsCreateSimpleMonitor"]["errors"], monitor, "create"
        )
        monitor.guid = r["data"]["syntheticsCreateSimpleMonitor"]["monitor"]["guid"]
        monitor.id = r["data"]["syntheticsCreateSimpleMonitor"]["monitor"]["id"]
        logger.info(
            "Monitor created with GUID %s, waiting for changes to be reflected in API",
            monitor.guid,
        )
        self.__wait_for_monitor_to_exist(monitor)

    def update_monitor(self, monitor: SyntheticMonitorBase):
        logger.info(
            "Updating synthetic monitor %s with GUID %s", monitor.name, monitor.guid
        )
        query_template = self.jinja_env.from_string(monitor.J2_UPDATE_QUERY)
        query = query_template.render(monitor=monitor)
        r = self.run_query(query=query)
        logger.debug(r)
        monitor.guid = r["data"]["syntheticsUpdateSimpleBrowserMonitor"]["monitor"][
            "guid"
        ]
        monitor.id = r["data"]["syntheticsUpdateSimpleBrowserMonitor"]["monitor"]["id"]
        self.__wait_for_monitor_to_exist(monitor=monitor)

    def __wait_for_monitor_to_exist(self, monitor):
        """
        Monitor changes take time to propagate in NR, so this will wait until the
        change can be seen in the API before continuing.
        At the end of the loop there's another small pause, since the change may only be
        partially propagated but we can't really check any further.
        """
        if not self.wait_for_propegation:
            return
        _time = 0
        remote_monitor_def = None
        while monitor != remote_monitor_def:
            if _time > self.propegation_timeout:
                raise Exception(
                    "Timedout waiting for new monitor to exist in New Relic API"
                )
            time.sleep(3)
            _time += 3
            remote_monitor_def = self.get_monitor_by_name_and_account(
                name=monitor.name, account_id=monitor.account_id
            )

    def __wait_for_monitor_to_not_exist(self, monitor):
        if not self.wait_for_propegation:
            return
        _time = 0
        remote_monitor_def = True
        while remote_monitor_def:
            if _time > self.propegation_timeout:
                raise Exception(
                    "Timedout waiting for new monitor to be deleted in New Relic API"
                )
            time.sleep(3)
            _time += 3
            remote_monitor_def = self.get_monitor_by_name_and_account(
                name=monitor.name, account_id=monitor.account_id
            )

    def raise_for_errors(self, errors, monitor, action):
        if not errors:
            return

        try:
            raise SyntheticMonitorQueryError(
                error_descriptions=[error["description"] for error in errors],
                monitor=monitor,
                action=action,
            )
        except KeyError:
            raise SyntheticMonitorQueryError(
                error_descriptions=errors,
                monitor=monitor,
                action=action,
            )

import logging
import time

from ansible_collections.newrelic.core.plugins.module_utils.models.synthetic import (
    SyntheticMonitorBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.api.nerdgraph_api_base import (
    NerdGraphApiBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.graphql.queries.synthetic import (
    SyntheticMonitorBaseClassQueries,
)


logger = logging.getLogger(__name__)


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
                % name
            )
        )

        if len(existing_monitors) == 1:
            return existing_monitors[0]
        elif not existing_monitors:
            return None
        else:
            raise Exception("Multiple synthetic monitors matched name query....")

    def get_monitors_from_query(
        self, entity_search_query: str, cursor: str = ""
    ) -> list:
        logger.info("Getting monitors from search '%s'", entity_search_query)
        query = SyntheticMonitorBaseClassQueries.monitor_search(
            entity_search_query=entity_search_query,
            cursor=cursor,
        )
        r = self.run_query(query=query)
        query_monitors, next_cursor = (
            SyntheticMonitorBaseClassQueries.parse_search_response(response=r)
        )
        logger.info(
            "Found %s monitors. Next cursor is %s", len(query_monitors), next_cursor
        )
        found_monitors = []
        for monitor_data in query_monitors:
            found_monitors += [SyntheticMonitorBase.from_api_data(monitor_data)]
        return found_monitors, next_cursor

    def delete_monitor(self, monitor: SyntheticMonitorBase) -> str:
        logger.info(
            "Deleting synthetic monitor %s with GUID %s", monitor.name, monitor.guid
        )
        query = SyntheticMonitorBaseClassQueries.delete(monitor=monitor)
        r = self.run_query(query=query)
        self.__wait_for_monitor_to_not_exist(monitor=monitor)
        return SyntheticMonitorBaseClassQueries.parse_delete_response(response=r)

    def create_monitor(self, monitor: SyntheticMonitorBase):
        logger.info("Creating synthetic monitor %s", monitor.name)
        query = SyntheticMonitorBaseClassQueries.create(monitor=monitor)
        r = self.run_query(query=query)
        SyntheticMonitorBaseClassQueries.parse_create_response(
            response=r, monitor=monitor
        )
        logger.info(
            "Monitor created with GUID %s, waiting for changes to be reflected in API",
            monitor.guid,
        )
        self.__wait_for_monitor_to_exist(monitor)

    def update_monitor(self, monitor: SyntheticMonitorBase):
        logger.info(
            "Updating synthetic monitor %s with GUID %s", monitor.name, monitor.guid
        )
        query = SyntheticMonitorBaseClassQueries.update(monitor=monitor)
        r = self.run_query(query=query)
        SyntheticMonitorBaseClassQueries.parse_update_response(
            response=r, monitor=monitor
        )
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

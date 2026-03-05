import logging
from typing import Generator

from ansible_collections.newrelic.core.plugins.module_utils.graphql.queries.change_tracking import (
    ChangeTrackingDeploymentQueries,
)
from ansible_collections.newrelic.core.plugins.module_utils.api.nerdgraph_api_base import (
    NerdGraphApiBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.models.change_tracking import (
    DeploymentEvent,
)


logger = logging.getLogger(__name__)


class CreateDeploymentQueryError(Exception):
    def __init__(self, error_descriptions, events, action):
        self.events = events
        self.error_descriptions = error_descriptions
        self.action = action
        super().__init__(
            "Failed to %s deployment events with version %s because %s"
            % (action, events[0].version, error_descriptions)
        )


class ChangeTrackingApi(NerdGraphApiBase):
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)


class ChangeTrackingDeploymentApi(ChangeTrackingApi):
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    def get_deployment_events_for_entity_guid(
        self,
        entity_guid: str,
        event_search_query: str = None,
        start_time: int = None,
        end_time: int = None,
    ) -> Generator[DeploymentEvent, None, None]:
        logger.info("Getting deployment events from entity guid '%s'", entity_guid)
        query = ChangeTrackingDeploymentQueries.entity_search(
            guid=entity_guid,
            entity_search_query=event_search_query,
            start_time=start_time,
            end_time=end_time
        )
        r = self.run_query(query=query.to_string())
        try:
            query_events = r["data"]["actor"]["entity"]["deploymentSearch"]["results"]
        except KeyError as e:
            logger.fatal("Encountered key error on '%s'", e)
            logger.fatal("response=%s", r)
            raise Exception("Query response did not match excepted format")

        logger.info("Found %s deployment events.", len(query_events))
        for event_data in query_events:
            yield self.__create_deployment_event_from_data(event_data)

    def __create_deployment_event_from_data(self, event_data):
        return DeploymentEvent.from_api_data(event_data)

    def create_deployment_events(self, events: list[DeploymentEvent]):
        logger.info(
            "Creating change tracking deployment events for version %s",
            events[0].version,
        )
        query = ChangeTrackingDeploymentQueries.create(events[0])
        r = self.run_query(query=query.to_string())
        logger.debug(r)
        self.raise_for_errors(r, events, "create")
        for response_output in r["data"]["changeTrackingCreateDeployment"]:
            for event in events:
                if event.id is not None:
                    continue
                if event.entity_guid != response_output["entityGuid"]:
                    continue
                event.id = response_output["deploymentId"]
                logger.info(
                    "Deployment event created with ID %s",
                    event.id,
                )

    def raise_for_errors(self, response, events, action):
        if not response.get("errors"):
            return

        try:
            raise CreateDeploymentQueryError(
                error_descriptions=[
                    error["message"] for error in response.get("errors")
                ],
                events=events,
                action=action,
            )
        except KeyError:
            raise CreateDeploymentQueryError(
                error_descriptions=response.get("errors"),
                events=events,
                action=action,
            )

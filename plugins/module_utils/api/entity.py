import logging
from typing import Generator

from ansible_collections.newrelic.core.plugins.module_utils.graphql.queries.entity import (
    EntityQueries,
)
from ansible_collections.newrelic.core.plugins.module_utils.models.entity import (
    Entity,
)
from ansible_collections.newrelic.core.plugins.module_utils.api.nerdgraph_api_base import (
    NerdGraphApiBase,
)


logger = logging.getLogger(__name__)


class EntityApi(NerdGraphApiBase):
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

    def get_entity_by_guid_and_account_id(self, guid, account_id) -> Entity:
        logger.info("Looking up entity with guid %s in account %s", guid, account_id)
        entity_search_query = "id = '%s' and accountId = '%s'" % (guid, account_id)
        for entity in self.get_entities_by_search_query(
            entity_search_query=entity_search_query
        ):
            return entity

        return None

    def get_entities_by_search_query(
        self, entity_search_query: str
    ) -> Generator[Entity, None, None]:
        logger.info("Looking up entity with query %s", entity_search_query)
        query = EntityQueries.entity_search(entity_search_query=entity_search_query)
        r = self.run_query(query=query)

        for entity_data in r["data"]["actor"]["entitySearch"]["results"]["entities"]:
            yield Entity.from_api_data(entity_data)

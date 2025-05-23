import logging

from ansible_collections.newrelic.core.plugins.module_utils.entity.query_templates import (
    EntityQueryTemplates,
)
from ansible_collections.newrelic.core.plugins.module_utils.entity.objects import (
    Entity,
)
from ansible_collections.newrelic.core.plugins.module_utils.nerdgraph_api_base import (
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

    def get_entity_by_guid(self, guid):
        logger.info("Looking up entity with guid %s", guid)
        query_template = self.jinja_env.from_string(
            EntityQueryTemplates.j2_get_from_search()
        )
        entity_search_query = "id = '%s'" % guid
        query = query_template.render(entity_search_query=entity_search_query)
        logger.debug("query=%s", "".join(query.split()))
        r = self.run_query(query=query)
        if r["data"]["actor"]["entitySearch"]["count"] != 1:
            raise Exception("Could not find entity with guid %s" % guid)

        return Entity.from_api_data(
            r["data"]["actor"]["entitySearch"]["results"]["entities"][0]
        )

import logging
import json
import time
import random

from ansible_collections.newrelic.core.plugins.module_utils.graphql.errors import (
    ApiRateLimitError,
)
from ansible_collections.newrelic.core.plugins.module_utils.graphql.response_parser import (
    GraphQLResponseParser,
)
from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
)

MISSING_IMPORTS = set()
try:
    import requests
except ImportError:
    MISSING_IMPORTS.add("requests")


logger = logging.getLogger(__name__)


class NerdGraphApiBase:
    def __init__(
        self,
        api_key: str,
        wait_for_propegation: bool = True,
        propegation_timeout: int = 10,
    ):
        if MISSING_IMPORTS:
            raise Exception(
                "Missing required python package(s): %s" % ", ".join(MISSING_IMPORTS)
            )
        self.default_headers = {"Api-Key": api_key}
        self.api_base_url = "https://api.newrelic.com/graphql"
        self.wait_for_propegation = wait_for_propegation
        self.propegation_timeout = propegation_timeout

    def run_query(
        self, query: GraphQLQuery, response_handler: GraphQLResponseParser = None
    ):
        try:
            r = requests.post(
                url=self.api_base_url,
                headers=dict(
                    self.default_headers, **{"Content-type": "application/json"}
                ),
                data=json.dumps({"query": query.to_gql_string()}),
            )
            self.handle_query_errors(r, query, response_handler)
        except ApiRateLimitError as e:
            logger.warning("%s", e)
            x = random.randrange(0, 15, 1)
            logger.info("Retrying in %s seconds", x)
            time.sleep(x)
            r = requests.post(
                url=self.api_base_url,
                headers=dict(
                    self.default_headers, **{"Content-type": "application/json"}
                ),
                data=json.dumps({"query": query.to_gql_string()}),
            )
            self.handle_query_errors(r, query, response_handler)

        return r.json()

    def handle_query_errors(
        self,
        response,
        query: GraphQLQuery,
        response_handler: GraphQLResponseParser = None,
    ):
        if not response_handler:
            response_handler = GraphQLResponseParser()
        response.raise_for_status()
        response_handler.raise_for_generic_query_errors(
            query=query, response=response.json()
        )

import logging

from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
)

from ansible_collections.newrelic.core.plugins.module_utils.graphql.errors import (
    GraphQLQueryError,
    GraphQLValidationError,
    ApiRateLimitError,
)


logger = logging.getLogger(__name__)


class GraphQLResponseParser:
    def raise_for_generic_query_errors(self, query: GraphQLQuery, response: dict):
        errors = response.get("errors", [])
        if not errors:
            return

        if len(errors) > 1:
            logger.fatal("errors=%s", errors)
            raise Exception(
                "More than one error was reported by the API. This scenario is not supported by the module code."
            )

        if errors[0].get("description", "").startswith("Rate limit exceeded"):
            raise ApiRateLimitError(errors[0])

        if errors[0].get("message", "").startswith("Validation Error"):
            raise GraphQLValidationError(response, query)

        raise GraphQLQueryError(response, query)

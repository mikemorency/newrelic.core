from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
)


class GraphQLResponseParsingError(Exception):
    def __init__(self, response, error: Exception, msg: str = None):
        if not msg:
            msg = "Unable to parse the GraphQL response, got error: %s" % error
        super().__init__(msg)
        self.response = response
        self.error = error

        def to_json(self):
            return {
                "response": self.response,
                "error_type": str(type(self.error)),
                "error_msg": str(self.error),
            }


class GraphQLQueryError(Exception):
    def __init__(self, response, query: GraphQLQuery, msg: str = None):
        if not msg:
            msg = "An error was returned while executing a query"
        super().__init__(msg)
        self.response = response
        self.query = query

    def to_json(self):
        return {
            "response": self.response,
            "query": self.query,
            "query_graphql_string": self.query.to_gql_string(),
        }


class GraphQLValidationError(GraphQLQueryError):
    def __init__(self, response, query):
        super().__init__(
            response, query, msg="There was a validation error with a query."
        )
        self.errors = []
        for error in response["errors"]:
            for val_err in error["extensions"]["validationErrors"]:
                self.errors.append(val_err["reason"])

    def to_json(self):
        return {"errors": self.errors}


class ApiRateLimitError(Exception):
    def __init__(self, error):
        super().__init__(error)

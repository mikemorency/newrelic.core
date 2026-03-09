from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
    Field,
)

from ansible_collections.newrelic.core.plugins.module_utils.models.alert_policy import (
    AlertPolicy,
)


class AlertPolicyQueries:
    @staticmethod
    def policy_search(account_id: int, search_query: str = None, cursor: str = None):
        gqlquery = GraphQLQuery(operation="query")

        policies_results_subfield = Field(
            name="policies", subfields=["id", "name", "accountId", "incidentPreference"]
        )
        policies_search_field = Field(
            name="policiesSearch",
            arguments={"searchCriteria": search_query, "cursor": cursor},
            subfields=["totalCount", "nextCursor", policies_results_subfield],
        )

        alerts_field = Field(name="alerts", subfields=[policies_search_field])

        account_field = Field(
            name="account", arguments={"id": int(account_id)}, subfields=[alerts_field]
        )

        actor_field = Field(name="actor", subfields=[account_field])

        gqlquery.fields.append(actor_field)
        return gqlquery

    @staticmethod
    def delete(policy: AlertPolicy):
        gqlquery = GraphQLQuery(operation="mutation")

        delete_field = Field(
            name="alertsPolicyDelete",
            arguments={"accountId": int(policy.account_id), "id": int(policy.id)},
            subfields=["id"],
        )

        gqlquery.fields.append(delete_field)
        return gqlquery

    @staticmethod
    def _policy_to_query_dict(policy: AlertPolicy):
        policy_dict = dict(
            name=policy.name, incidentPreference=policy.incident_preference
        )

        return policy_dict

    @staticmethod
    def create(policy: AlertPolicy, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        create_field = Field(
            name="alertsPolicyCreate",
            arguments=dict(
                accountId=int(policy.account_id),
                policy=AlertPolicyQueries._policy_to_query_dict(policy),
            ),
            subfields=["id", "name", "incidentPreference"],
        )

        gqlquery.fields.append(create_field)
        return gqlquery

    @staticmethod
    def update(policy: AlertPolicy, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        update_field = Field(
            name="alertsPolicyUpdate",
            arguments=dict(
                accountId=int(policy.account_id),
                id=int(policy.id),
                policy=AlertPolicyQueries._policy_to_query_dict(policy),
            ),
            subfields=["id", "name", "incidentPreference"],
        )

        gqlquery.fields.append(update_field)
        return gqlquery

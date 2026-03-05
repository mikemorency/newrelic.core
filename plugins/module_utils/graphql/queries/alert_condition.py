from enum import Enum

from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
    Field,
    add_to_dict_if_not_none
)

from ansible_collections.newrelic.core.plugins.module_utils.models.alert_condition import (
    NrqlAlertConditionBase,
    NrqlStaticAlertCondition,
    DataAggregationMethod
)


class NrqlBaseClassAlertConditionQueries():
    @staticmethod
    def condition_search(account_id: int, search_query: str = None, cursor: str = None):
        gqlquery = GraphQLQuery(operation="query")

        nrql_results_subfield = Field(name="nrql", subfields=["query"])
        signal_results_subfield = Field(
            name="signal",
            subfields=[
                "aggregationDelay",
                "aggregationMethod",
                "aggregationTimer",
                "aggregationWindow",
                "evaluationDelay",
                "fillOption",
                "fillValue",
                "slideBy"
            ]
        )
        terms_results_subfield = Field(
            name="terms",
            subfields=[
                "priority",
                "operator",
                "threshold",
                "thresholdDuration",
                "thresholdOccurrences"
            ]
        )
        conditions_results_subfield = Field(
            name="nrqlConditions",
            subfields=[
                "description",
                "enabled",
                "entityGuid",
                "id",
                "name",
                nrql_results_subfield,
                "runbookUrl",
                "policyId",
                signal_results_subfield,
                terms_results_subfield,
                "type"
            ]
        )

        conditions_search_field = Field(
            name="nrqlConditionsSearch",
            arguments={"searchCriteria": search_query, "cursor": cursor},
            subfields=[
                "totalCount",
                "nextCursor",
                conditions_results_subfield
            ]
        )

        alerts_field = Field(name="alerts", subfields=[conditions_search_field])

        account_field = Field(
            name="account",
            arguments={"id": int(account_id)},
            subfields=[
                alerts_field
            ]
        )

        actor_field = Field(name="actor", subfields=[account_field])

        gqlquery.fields.append(actor_field)
        return gqlquery

    @staticmethod
    def delete(condition: NrqlAlertConditionBase):
        gqlquery = GraphQLQuery(operation="mutation")

        condition_delete_field = Field(
            name="alertsConditionDelete",
            arguments={"accountId": int(condition.account_id), "id": condition.id},
            subfields=["id"]
        )

        gqlquery.fields.append(condition_delete_field)
        return gqlquery


class NrqlStaticAlertAlertConditionQueries(NrqlBaseClassAlertConditionQueries):
    @staticmethod
    def _condition_to_query_dict(condition: NrqlStaticAlertCondition):
        class ConditionValueFunction(str, Enum):
            SINGLE_VALUE = "SINGLE_VALUE"

        signal_dict = dict(
            aggregationWindow=condition.data_aggregation_window,
            aggregationMethod=condition.data_aggregation_method
        )
        add_to_dict_if_not_none(signal_dict, "slideBy", condition.data_slide_by)
        if condition.data_aggregation_method is not DataAggregationMethod.EVENT_TIMER:
            signal_dict["aggregationDelay"] = condition.data_aggregation_delay

        if condition.data_aggregation_method is not DataAggregationMethod.EVENT_FLOW:
            signal_dict["aggregationTimer"] = condition.data_aggregation_timer

        terms_list = list()
        for term in condition.incident_terms:
            terms_list.append(dict(
                threshold=term.threshold,
                thresholdDuration=term.duration,
                thresholdOccurrences=term.occurrences,
                operator=term.operator,
                priority=term.priority
            ))

        condition_dict = dict(
            name=condition.name,
            enabled=bool(condition.enabled),
            nrql=dict(
                query=condition.nrql_query
            ),
            signal=signal_dict,
            terms=terms_list,
            valueFunction=ConditionValueFunction.SINGLE_VALUE,
            violationTimeLimitSeconds=86400
        )
        add_to_dict_if_not_none(condition_dict, "description", condition.description)
        add_to_dict_if_not_none(condition_dict, "runbookUrl", condition.runbook_url)

        return condition_dict

    @staticmethod
    def create(condition: NrqlStaticAlertCondition, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        create_field = Field(
            name="alertsNrqlConditionStaticCreate",
            arguments=dict(
                accountId=int(condition.account_id),
                policyId=int(condition.policy_id),
                condition=NrqlStaticAlertAlertConditionQueries._condition_to_query_dict(condition)
            ),
            subfields=[
                "id",
                "entityGuid"
            ]
        )

        gqlquery.fields.append(create_field)
        return gqlquery

    @staticmethod
    def update(condition: NrqlStaticAlertCondition, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        update_field = Field(
            name="alertsNrqlConditionStaticUpdate",
            arguments=dict(
                accountId=int(condition.account_id),
                id=condition.id,
                condition=NrqlStaticAlertAlertConditionQueries._condition_to_query_dict(condition)
            ),
            subfields=[
                "id",
                "entityGuid"
            ]
        )

        gqlquery.fields.append(update_field)
        return gqlquery

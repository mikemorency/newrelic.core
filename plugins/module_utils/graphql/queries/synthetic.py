from enum import Enum
from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
    Field,
    add_to_dict_if_not_none
)

from ansible_collections.newrelic.core.plugins.module_utils.models.synthetic import (
    SyntheticMonitorBase,
    PingSyntheticMonitor
)


class SyntheticMonitorBaseClassQueries():
    @staticmethod
    def monitor_search(entity_search_query: str = None, cursor: str = None):
        gqlquery = GraphQLQuery(operation="query")

        tags_results_subfield = Field(name="tags", subfields=["key", "values"])
        monitor_summary_results_subfield = Field(
            name="monitorSummary",
            subfields=[
                "locationsRunning",
                "status",
                "locationsFailing",
                "successRate"
            ]
        )
        monitor_entity_outline_results_subfield = Field(
            name="... on SyntheticMonitorEntityOutline",
            subfields=[
                "guid",
                "name",
                "accountId",
                "entityType",
                "monitorId",
                "monitorType",
                "monitoredUrl",
                "period",
                monitor_summary_results_subfield,
                tags_results_subfield,
                "type"
            ]
        )
        entities_results_subfield = Field(name="entities", subfields=[monitor_entity_outline_results_subfield])
        results_field = Field(
            name="results",
            arguments=dict(cursor=cursor) if cursor else dict(),
            subfields=[
                "nextCursor",
                entities_results_subfield
            ]
        )

        search_field = Field(
            name="entitySearch",
            arguments={"query": entity_search_query},
            subfields=[results_field]
        )

        actor_field = Field(name="actor", subfields=[search_field])

        gqlquery.fields.append(actor_field)
        return gqlquery

    @staticmethod
    def delete(monitor: SyntheticMonitorBase):
        gqlquery = GraphQLQuery(operation="mutation")

        delete_field = Field(
            name="syntheticsDeleteMonitor",
            arguments={"guid": monitor.guid},
            subfields=["deletedGuid"]
        )

        gqlquery.fields.append(delete_field)
        return gqlquery


class PingSyntheticMonitorQueries(SyntheticMonitorBaseClassQueries):
    @staticmethod
    def _monitor_to_query_dict(monitor: PingSyntheticMonitor):
        class MonitorStatus(str, Enum):
            ENABLED = "ENABLED"
            DISABLED = "DISABLED"

        locations_dict = dict()
        add_to_dict_if_not_none(locations_dict, "public", monitor.public_locations)
        if monitor.private_locations:
            locations_dict['private'] = [{"guid":guid} for guid in monitor.private_locations]

        advanced_options_dict = dict(useTlsValidation=monitor.verify_ssl)
        add_to_dict_if_not_none(advanced_options_dict, "responseValidationText", monitor.validation_string)

        monitor_dict = dict(
            locations=locations_dict,
            name=monitor.name,
            period=monitor.period,
            status=MonitorStatus.ENABLED if monitor.enabled else MonitorStatus.DISABLED,
            uri=monitor.url,
            advancedOptions=advanced_options_dict
        )

        return monitor_dict

    @staticmethod
    def create(monitor: PingSyntheticMonitor, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        errors_subfield = Field(name="errors", subfields=["description", "type"])
        monitor_subfield = Field(name="monitor", subfields=["guid", "id", "name"])

        create_field = Field(
            name="syntheticsCreateSimpleMonitor",
            arguments=dict(
                accountId=int(monitor.account_id),
                monitor=PingSyntheticMonitorQueries._monitor_to_query_dict(monitor)
            ),
            subfields=[errors_subfield, monitor_subfield]
        )

        gqlquery.fields.append(create_field)
        return gqlquery

    @staticmethod
    def update(monitor: PingSyntheticMonitor, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        errors_subfield = Field(name="errors", subfields=["description", "type"])
        monitor_subfield = Field(name="monitor", subfields=["guid", "id", "name"])

        create_field = Field(
            name="syntheticsUpdateSimpleBrowserMonitor",
            arguments=dict(
                guid=monitor.guid,
                monitor=PingSyntheticMonitorQueries._monitor_to_query_dict(monitor)
            ),
            subfields=[errors_subfield, monitor_subfield]
        )

        gqlquery.fields.append(create_field)
        return gqlquery

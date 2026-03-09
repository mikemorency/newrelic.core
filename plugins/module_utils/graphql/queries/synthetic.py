from enum import Enum
from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
    Field,
    add_to_dict_if_not_none,
)

from ansible_collections.newrelic.core.plugins.module_utils.models.synthetic import (
    SyntheticMonitorBase,
    PingSyntheticMonitor,
    CertSyntheticMonitor,
)

from ansible_collections.newrelic.core.plugins.module_utils.graphql.errors import (
    GraphQLResponseParsingError,
)


class SyntheticMonitorQueryError(Exception):
    def __init__(self, error_descriptions, monitor, action):
        self.monitor = monitor
        self.error_descriptions = error_descriptions
        self.action = action
        super().__init__(
            "Failed to %s monitor %s because %s"
            % (action, monitor.name, error_descriptions)
        )


def raise_for_errors(errors, monitor, action):
    if not errors:
        return

    try:
        raise SyntheticMonitorQueryError(
            error_descriptions=[error["description"] for error in errors],
            monitor=monitor,
            action=action,
        )
    except KeyError:
        raise SyntheticMonitorQueryError(
            error_descriptions=errors,
            monitor=monitor,
            action=action,
        )


class MonitorStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class SyntheticMonitorBaseClassQueries:
    @staticmethod
    def monitor_search(entity_search_query: str = None, cursor: str = None):
        gqlquery = GraphQLQuery(operation="query")

        tags_results_subfield = Field(name="tags", subfields=["key", "values"])
        monitor_summary_results_subfield = Field(
            name="monitorSummary",
            subfields=["locationsRunning", "status", "locationsFailing", "successRate"],
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
                "type",
            ],
        )
        entities_results_subfield = Field(
            name="entities", subfields=[monitor_entity_outline_results_subfield]
        )
        results_field = Field(
            name="results",
            arguments=dict(cursor=cursor) if cursor else dict(),
            subfields=["nextCursor", entities_results_subfield],
        )

        search_field = Field(
            name="entitySearch",
            arguments={"query": entity_search_query},
            subfields=[results_field],
        )

        actor_field = Field(name="actor", subfields=[search_field])

        gqlquery.fields.append(actor_field)
        return gqlquery

    @staticmethod
    def parse_search_response(response: dict) -> (list, str):
        try:
            query_conditions = response["data"]["actor"]["entitySearch"]["results"][
                "entities"
            ]
            cursor = response["data"]["actor"]["entitySearch"]["results"]["nextCursor"]
        except KeyError as e:
            raise GraphQLResponseParsingError(
                response=response,
                error=e,
                msg="Unable to parse alert condition search response due to unexpected response format.",
            )

        return query_conditions, cursor

    @staticmethod
    def delete(monitor: SyntheticMonitorBase):
        gqlquery = GraphQLQuery(operation="mutation")

        delete_field = Field(
            name="syntheticsDeleteMonitor",
            arguments={"guid": monitor.guid},
            subfields=["deletedGuid"],
        )

        gqlquery.fields.append(delete_field)
        return gqlquery

    @staticmethod
    def parse_delete_response(response: dict) -> str:
        try:
            return response["data"]["syntheticsDeleteMonitor"]["deletedGuid"]
        except KeyError as e:
            raise GraphQLResponseParsingError(
                response=response,
                error=e,
                msg="Unable to parse synthetic monitor delete response due to unexpected response format.",
            )

    @staticmethod
    def create(monitor: SyntheticMonitorBase):
        if isinstance(monitor, PingSyntheticMonitor):
            return PingSyntheticMonitorQueries.create(monitor)
        elif isinstance(monitor, CertSyntheticMonitor):
            return CertSyntheticMonitorQueries.create(monitor)

        raise Exception(
            f"Create query is not defined for monitor class {type(monitor)}"
        )

    @staticmethod
    def parse_create_response(response: dict, monitor: SyntheticMonitorBase):
        if isinstance(monitor, PingSyntheticMonitor):
            return PingSyntheticMonitorQueries.parse_create_response(
                monitor=monitor, response=response
            )
        elif isinstance(monitor, CertSyntheticMonitor):
            return CertSyntheticMonitorQueries.parse_create_response(
                monitor=monitor, response=response
            )

        raise Exception(
            f"Create response parser is not defined for monitor class {type(monitor)}"
        )

    @staticmethod
    def update(monitor: SyntheticMonitorBase):
        if isinstance(monitor, PingSyntheticMonitor):
            return PingSyntheticMonitorQueries.update(monitor)
        elif isinstance(monitor, CertSyntheticMonitor):
            return CertSyntheticMonitorQueries.update(monitor)

        raise Exception(
            f"Update query is not defined for monitor class {type(monitor)}"
        )

    @staticmethod
    def parse_update_response(response: dict, monitor: SyntheticMonitorBase):
        if isinstance(monitor, PingSyntheticMonitor):
            return PingSyntheticMonitorQueries.parse_update_response(
                monitor=monitor, response=response
            )
        elif isinstance(monitor, CertSyntheticMonitor):
            return CertSyntheticMonitorQueries.parse_update_response(
                monitor=monitor, response=response
            )

        raise Exception(
            f"Update response parser is not defined for monitor class {type(monitor)}"
        )


class PingSyntheticMonitorQueries(SyntheticMonitorBaseClassQueries):
    @staticmethod
    def _monitor_to_query_dict(monitor: PingSyntheticMonitor):
        locations_dict = dict()
        add_to_dict_if_not_none(locations_dict, "public", monitor.public_locations)
        if monitor.private_locations:
            locations_dict["private"] = [
                {"guid": guid} for guid in monitor.private_locations
            ]

        advanced_options_dict = dict(useTlsValidation=monitor.verify_ssl)
        add_to_dict_if_not_none(
            advanced_options_dict, "responseValidationText", monitor.validation_string
        )

        monitor_dict = dict(
            locations=locations_dict,
            name=monitor.name,
            period=monitor.period,
            status=MonitorStatus.ENABLED if monitor.enabled else MonitorStatus.DISABLED,
            uri=monitor.url,
            advancedOptions=advanced_options_dict,
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
                monitor=PingSyntheticMonitorQueries._monitor_to_query_dict(monitor),
            ),
            subfields=[errors_subfield, monitor_subfield],
        )

        gqlquery.fields.append(create_field)
        return gqlquery

    @staticmethod
    def parse_create_response(response: dict, monitor: PingSyntheticMonitor) -> None:
        try:
            raise_for_errors(
                errors=response["data"]["syntheticsCreateSimpleMonitor"]["errors"],
                monitor=monitor,
                action="create",
            )

            monitor.guid = response["data"]["syntheticsCreateSimpleMonitor"]["monitor"][
                "guid"
            ]
            monitor.id = response["data"]["syntheticsCreateSimpleMonitor"]["monitor"][
                "id"
            ]
        except KeyError as e:
            raise GraphQLResponseParsingError(
                response=response,
                error=e,
                msg="Unable to parse synthetic monitor create response due to unexpected response format.",
            )

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
                monitor=PingSyntheticMonitorQueries._monitor_to_query_dict(monitor),
            ),
            subfields=[errors_subfield, monitor_subfield],
        )

        gqlquery.fields.append(create_field)
        return gqlquery

    @staticmethod
    def parse_update_response(response: dict, monitor: PingSyntheticMonitor) -> None:
        try:
            raise_for_errors(
                errors=response["data"]["syntheticsUpdateSimpleBrowserMonitor"][
                    "errors"
                ],
                monitor=monitor,
                action="create",
            )
            monitor.guid = response["data"]["syntheticsUpdateSimpleBrowserMonitor"][
                "monitor"
            ]["guid"]
            monitor.id = response["data"]["syntheticsUpdateSimpleBrowserMonitor"][
                "monitor"
            ]["id"]
        except KeyError as e:
            raise GraphQLResponseParsingError(
                response=response,
                error=e,
                msg="Unable to parse synthetic monitor update response due to unexpected response format.",
            )


class CertSyntheticMonitorQueries(SyntheticMonitorBaseClassQueries):
    @staticmethod
    def _monitor_to_query_dict(monitor: CertSyntheticMonitor):
        locations_dict = dict()
        add_to_dict_if_not_none(locations_dict, "public", monitor.public_locations)
        if monitor.private_locations:
            locations_dict["private"] = [
                {"guid": guid} for guid in monitor.private_locations
            ]

        monitor_dict = dict(
            locations=locations_dict,
            name=monitor.name,
            period=monitor.period,
            status=MonitorStatus.ENABLED if monitor.enabled else MonitorStatus.DISABLED,
            domain=monitor.url,
        )
        add_to_dict_if_not_none(
            monitor_dict,
            "numberDaysToFailBeforeCertExpires",
            monitor.days_before_cert_expires_to_trigger_failure,
        )

        return monitor_dict

    @staticmethod
    def create(monitor: CertSyntheticMonitor, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        errors_subfield = Field(name="errors", subfields=["description", "type"])
        monitor_subfield = Field(name="monitor", subfields=["guid", "id", "name"])

        create_field = Field(
            name="syntheticsCreateCertCheckMonitor",
            arguments=dict(
                accountId=int(monitor.account_id),
                monitor=CertSyntheticMonitorQueries._monitor_to_query_dict(monitor),
            ),
            subfields=[errors_subfield, monitor_subfield],
        )

        gqlquery.fields.append(create_field)
        return gqlquery

    @staticmethod
    def parse_create_response(response: dict, monitor: CertSyntheticMonitor) -> None:
        try:
            raise_for_errors(
                errors=response["data"]["syntheticsCreateCertCheckMonitor"]["errors"],
                monitor=monitor,
                action="create",
            )
            monitor.guid = response["data"]["syntheticsCreateCertCheckMonitor"][
                "monitor"
            ]["guid"]
            monitor.id = response["data"]["syntheticsCreateCertCheckMonitor"][
                "monitor"
            ]["id"]
        except KeyError as e:
            raise GraphQLResponseParsingError(
                response=response,
                error=e,
                msg="Unable to parse synthetic monitor create response due to unexpected response format.",
            )

    @staticmethod
    def update(monitor: CertSyntheticMonitor, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery(operation="mutation")
        else:
            gqlquery = append_to_query

        errors_subfield = Field(name="errors", subfields=["description", "type"])
        monitor_subfield = Field(name="monitor", subfields=["guid", "id", "name"])

        create_field = Field(
            name="syntheticsUpdateCertCheckMonitor",
            arguments=dict(
                guid=monitor.guid,
                monitor=CertSyntheticMonitorQueries._monitor_to_query_dict(monitor),
            ),
            subfields=[errors_subfield, monitor_subfield],
        )

        gqlquery.fields.append(create_field)
        return gqlquery

    @staticmethod
    def parse_update_response(response: dict, monitor: CertSyntheticMonitor) -> None:
        try:
            raise_for_errors(
                errors=response["data"]["syntheticsUpdateCertCheckMonitor"]["errors"],
                monitor=monitor,
                action="create",
            )
            monitor.guid = response["data"]["syntheticsUpdateCertCheckMonitor"][
                "monitor"
            ]["guid"]
            monitor.id = response["data"]["syntheticsUpdateCertCheckMonitor"][
                "monitor"
            ]["id"]
        except KeyError as e:
            raise GraphQLResponseParsingError(
                response=response,
                error=e,
                msg="Unable to parse synthetic monitor update response due to unexpected response format.",
            )

import logging

from ansible_collections.newrelic.core.plugins.module_utils.graphql.queries.alert_condition import (
    NrqlBaseClassAlertConditionQueries,
    NrqlStaticAlertAlertConditionQueries,
)
from ansible_collections.newrelic.core.plugins.module_utils.api.nerdgraph_api_base import (
    NerdGraphApiBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.models.alert_condition import (
    NrqlAlertConditionBase,
)


logger = logging.getLogger(__name__)


class NrqlAlertConditionApi(NerdGraphApiBase):
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

    def get_condition_by_name_policy_and_account(self, name, policy_id, account_id):
        existing_conditions, _ = (  # pylint: disable=disallowed-name
            self.get_conditions_from_query(
                entity_search_query=dict(name=name, policyId=policy_id),
                account_id=account_id,
            )
        )
        if len(existing_conditions) == 1:
            return existing_conditions[0]
        elif not existing_conditions:
            return None
        else:
            raise Exception("Multiple alert conditions matched name query....")

    def get_conditions_from_query(
        self, entity_search_query: dict, account_id: str, cursor: str = ""
    ) -> list:
        logger.info("Getting conditions from search '%s'", entity_search_query)
        query = NrqlBaseClassAlertConditionQueries.condition_search(
            account_id=account_id, search_query=entity_search_query, cursor=cursor
        )
        r = self.run_query(query=query)
        query_conditions, cursor = (
            NrqlBaseClassAlertConditionQueries.parse_search_response(response=r)
        )

        found_conditions = []
        for condition_data in query_conditions:
            logger.debug(condition_data)
            found_conditions += [
                NrqlAlertConditionBase.from_api_data(
                    data=condition_data, account_id=account_id
                )
            ]
        return found_conditions, cursor

    def delete_condition(self, condition: NrqlAlertConditionBase) -> str:
        logger.info(
            "Deleting alert condition %s with ID %s",
            condition.name,
            condition.id,
        )
        r = self.run_query(
            query=NrqlBaseClassAlertConditionQueries.delete(condition=condition)
        )
        return NrqlBaseClassAlertConditionQueries.parse_delete_response(response=r)

    def create_condition(self, condition: NrqlAlertConditionBase):
        condition.validate_properties()
        if condition.entity_type == "STATIC":
            query = NrqlStaticAlertAlertConditionQueries.create(condition=condition)
        else:
            raise Exception("Unknown condition type %s" % condition.entity_type)
        r = self.run_query(query=query)
        NrqlStaticAlertAlertConditionQueries.parse_create_response(
            response=r, condition=condition
        )

    def update_condition(self, condition: NrqlAlertConditionBase):
        condition.validate_properties()
        if condition.entity_type == "STATIC":
            query = NrqlStaticAlertAlertConditionQueries.update(condition=condition)
        else:
            raise Exception("Unknown condition type %s" % condition.entity_type)
        r = self.run_query(query=query)
        NrqlStaticAlertAlertConditionQueries.parse_update_response(
            response=r, condition=condition
        )

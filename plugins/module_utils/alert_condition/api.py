import logging

from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.objects import (
    NrqlAlertConditionBase,
    NrqlStaticAlertCondition,
)
from ansible_collections.newrelic.core.plugins.module_utils.nerdgraph_api_base import (
    NerdGraphApiBase,
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
                entity_search_query='name: "%s", policyId: "%s"' % (name, policy_id),
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
        self, entity_search_query: str, account_id: str, cursor: str = ""
    ) -> list:
        logger.info("Getting conditions from search '%s'", entity_search_query)
        query_template = self.jinja_env.from_string(
            NrqlAlertConditionBase.J2_SEARCH_QUERY
        )
        query = query_template.render(
            entity_search_query=entity_search_query,
            account_id=account_id,
            cursor=cursor,
        )
        r = self.run_query(query=query)
        try:
            query_conditions = r["data"]["actor"]["account"]["alerts"][
                "nrqlConditionsSearch"
            ]["nrqlConditions"]
            cursor = r["data"]["actor"]["account"]["alerts"]["nrqlConditionsSearch"][
                "nextCursor"
            ]
        except KeyError as e:
            logger.fatal("Encountered key error on '%s'", e)
            logger.fatal("response=%s", r)
            raise Exception("Query response did not match excepted format")

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
        query_template = self.jinja_env.from_string(
            NrqlAlertConditionBase.J2_DELETE_QUERY
        )
        query = query_template.render(condition=condition)
        r = self.run_query(query=query)
        return r["data"]["alertsConditionDelete"]["id"]

    def create_condition(self, condition: NrqlAlertConditionBase):
        condition.validate_properties()
        if condition.entity_type == "STATIC":
            query_template = self.jinja_env.from_string(
                NrqlStaticAlertCondition.J2_CREATE_QUERY
            )
        else:
            raise Exception("Unknown condition type %s" % condition.entity_type)
        query = query_template.render(condition=condition)
        r = self.run_query(query=query)
        logger.debug(r)
        condition.id = r["data"]["alertsNrqlConditionStaticCreate"]["id"]
        condition.guid = r["data"]["alertsNrqlConditionStaticCreate"]["entityGuid"]

    def update_condition(self, condition: NrqlAlertConditionBase):
        condition.validate_properties()
        if condition.entity_type == "STATIC":
            query_template = self.jinja_env.from_string(
                NrqlStaticAlertCondition.J2_UPDATE_QUERY
            )
        else:
            raise Exception("Unknown condition type %s" % condition.entity_type)
        query = query_template.render(condition=condition)
        r = self.run_query(query=query)
        logger.debug(r)
        condition.id = r["data"]["alertsNrqlConditionStaticUpdate"]["id"]
        condition.guid = r["data"]["alertsNrqlConditionStaticUpdate"]["entityGuid"]

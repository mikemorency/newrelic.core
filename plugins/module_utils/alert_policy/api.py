import logging
import time

from ansible_collections.newrelic.core.plugins.module_utils.alert_policy.objects import (
    AlertPolicy,
)
from ansible_collections.newrelic.core.plugins.module_utils.nerdgraph_api_base import (
    NerdGraphApiBase,
)


logger = logging.getLogger(__name__)


class AlertPolicyApi(NerdGraphApiBase):
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

    def get_policy_by_name_and_account(self, name, account_id):
        existing_policies, _ = (  # pylint: disable=disallowed-name
            self.get_policies_from_query(
                entity_search_query='name: "%s"' % name, account_id=account_id
            )
        )
        if len(existing_policies) == 1:
            return existing_policies[0]
        elif not existing_policies:
            return None
        else:
            raise Exception("Multiple policies matched name query....")

    def get_policies_from_query(
        self, entity_search_query: str, account_id: str, cursor: str = ""
    ) -> list:
        logger.info("Getting policies from search '%s'", entity_search_query)
        query_template = self.jinja_env.from_string(AlertPolicy.J2_SEARCH_QUERY)
        query = query_template.render(
            entity_search_query=entity_search_query,
            account_id=account_id,
            cursor=cursor,
        )
        r = self.run_query(query=query)
        try:
            query_policies = r["data"]["actor"]["account"]["alerts"]["policiesSearch"][
                "policies"
            ]
            next_cursor = r["data"]["actor"]["account"]["alerts"]["policiesSearch"][
                "nextCursor"
            ]
        except KeyError as e:
            logger.fatal("Encountered key error on '%s'", e)
            logger.fatal("response=%s", r)
            raise Exception("Query response did not match excepted format")

        logger.info(
            "Found %s policies. Next cursor is %s", len(query_policies), next_cursor
        )
        found_policies = []
        for policy_data in query_policies:
            found_policies += [AlertPolicy.from_api_data(policy_data)]
        return found_policies, next_cursor

    def create_policy(self, alert_policy: AlertPolicy):
        logger.info("Creating alert policy %s", alert_policy.name)
        query_template = self.jinja_env.from_string(AlertPolicy.J2_CREATE_QUERY)
        query = query_template.render(alert_policy=alert_policy)
        r = self.run_query(query=query)
        logger.debug(r)
        alert_policy.id = r["data"]["alertsPolicyCreate"]["id"]
        self.__wait_for_policy_creation(alert_policy)

    def update_policy(self, alert_policy: AlertPolicy):
        logger.info("Updating policy %s", alert_policy.name)
        query_template = self.jinja_env.from_string(alert_policy.J2_UPDATE_QUERY)
        query = query_template.render(alert_policy=alert_policy)
        self.run_query(query=query)

    def delete_policy(self, alert_policy: AlertPolicy) -> str:
        logger.info(
            "Deleting alert policy %s with ID %s",
            alert_policy.name,
            alert_policy.id,
        )
        query_template = self.jinja_env.from_string(alert_policy.J2_DELETE_QUERY)
        query = query_template.render(alert_policy=alert_policy)
        r = self.run_query(query=query)
        logger.debug(r)
        return r["data"]["alertsPolicyDelete"]["id"]

    def __wait_for_policy_creation(self, alert_policy):
        if not self.wait_for_propegation:
            return
        _time = 0
        remote_policy_def = None
        while alert_policy != remote_policy_def:
            if _time > self.propegation_timeout:
                raise Exception(
                    "Timedout waiting for new alert policy to exist in New Relic API"
                )
            time.sleep(3)
            _time += 3
            remote_policy_def = self.get_policy_by_name_and_account(
                name=alert_policy.name, account_id=alert_policy.account_id
            )

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: nrql_static_alert_condition
short_description: Manage a NRQL static alert condition
description:
    - Creates, updates, or deletes an alert condition based on a NRQL query.
    - This is a generic version of other more specific modules like synthetic_monitor_alert_condition

extends_documentation_fragment:
    - newrelic.core.module_base

options:
    name:
        description:
            - The exact name of the synthetic monitor to manage
        required: true
        type: str
    state:
        description:
            - Controls if the alert should be 'present' or 'absent'
        required: false
        default: present
        type: str
        choices: [present, absent]
    enabled:
        description:
            - Controls if the alert should be enabled or disabled
        required: false
        default: True
        type: bool
    nrql_query:
        description:
            - The NRQL query from which this condition should pull data
            - Required when state is present
        required: false
        type: str
    policy_id:
        description:
            - The alert policy ID to which this condition should be added
        required: true
        type: str
    runbook_url:
        description:
            - A url to runbook documentation for handling this alert
        required: false
        type: str
    description:
        description:
            - A description for the condition to help other user's understand its purpose
        required: false
        type: str
    critical_incident:
        description:
            - A dictionary describing when a critical incident should be opened
        type: dict
        suboptions:
            threshold:
                description:
                    - The value returned by the NRQL query that triggers an incident
                required: true
                type: int
            operator:
                description:
                    - Controls when an incident is created by comparing the current query value
                      with the threshold value defined.
                    - For example, if the operator is BELOW and the threshold is 1, an incident
                      will be created if the query returns a value below 1
                required: true
                type: str
                choices: [ABOVE, BELOW, ABOVE_OR_EQUALS, BELOW_OR_EQUALS, EQUALS, NOT_EQUALS]
            duration:
                description:
                    - Controls how long the query value needs to be violating the threshold before
                      an incident is created
                default: 600
                type: int
            occurrences:
                description:
                    - Controls how if a new incident is opened if the query value re-violates the
                      threshold while another incident is open
                default: ALL
                choices: [ALL, AT_LEAST_ONCE]
                type: str
    warning_incident:
        description:
            - A dictionary describing when a warning incident should be opened
        type: dict
        suboptions:
            threshold:
                description:
                    - The value returned by the NRQL query that triggers an incident
                required: true
                type: int
            operator:
                description:
                    - Controls when an incident is created by comparing the current query value
                      with the threshold value defined.
                    - For example, if the operator is BELOW and the threshold is 1, an incident
                      will be created if the query returns a value below 1
                required: true
                type: str
                choices: [ABOVE, BELOW, ABOVE_OR_EQUALS, BELOW_OR_EQUALS, EQUALS, NOT_EQUALS]
            duration:
                description:
                    - Controls how long the query value needs to be violating the threshold before
                      an incident is created
                default: 600
                type: int
            occurrences:
                description:
                    - Controls how if a new incident is opened if the query value re-violates the
                      threshold while another incident is open
                default: ALL
                choices: [ALL, AT_LEAST_ONCE]
                type: str
    data_aggregation_window:
        description:
            - The window of time in seconds to use when aggregating data
        default: 60
        type: int
    data_aggregation_method:
        description:
            - The method to use when aggregation data collected by the query
        default: EVENT_FLOW
        type: str
        choices: [EVENT_TIMER, EVENT_FLOW, CADENCE]
    data_aggregation_timer:
        description:
            - The time in seconds used to wait for data to aggregate
            - This option is only used if the aggregation method is EVENT_TIMER
        default: 60
        type: int
    data_aggregation_delay:
        description:
            - The delay in seconds before the condition should be evaluated against data
            - This option is only used if the aggregation method is EVENT_FLOW or CADENCE
        default: 120
        type: int
    data_aggregation_sliding_window:
        description:
            - The amount of seconds the signal should be shifted
        required: false
        type: int
    evaluation_delay:
        description:
            - THe length of time after data is received before it is evaluated.
        type: int
        required: false
"""

EXAMPLES = r"""
- name: Create General Alert
  newrelic.core.nrql_static_alert_condition:
    name: Host Not Reporting
    nrql_query: >-
      SELECT count('cpuPercent') FROM SystemSample FACET entityName
    policy_id: "{{ _infra_policy.policy_id }}"
    data_aggregation_window: 60
    data_aggregation_method: EVENT_FLOW
    data_aggregation_delay: 120
    description: >-
      Host is not reporting because it is offline or the New Relic infrastructure service is stopped.
    critical_incident:
      operator: BELOW
      threshold: 1
      duration: 300
      occurrences: ALL
"""

RETURN = r"""
condition:
    description: Dictionary holding condition identifiers if one was created or updated
    type: dict
    returned: always
    sample: {
        'name': "my-condition",
        'id': "123345",
        'guid': "FSDAJRFOIJ3E21321JL321"
    }
"""
from ansible.module_utils.basic import AnsibleModule

import logging
from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.objects import (
    NrqlStaticAlertCondition,
    IncidentTerm,
)
from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.api import (
    NrqlAlertConditionApi,
)
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)


logger = logging.getLogger(__name__)


class NrqlStaticAlertConditionModule(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = NrqlAlertConditionApi(
            self.params["api_key"],
            self.params["wait_for_propegation"],
            self.params["propegation_timeout"],
        )
        self.live_condition = None

    def get_live_condition_from_newrelic(self):
        """
        This function attempts to lookup the alert condition from New Relic.
        It is not in the init method so we can catch any NR query errors that
        are raised and exit the module with them.
        Returns:
          AlertPolicy or None
        """
        self.live_condition = self.api.get_condition_by_name_policy_and_account(
            name=self.params["name"],
            policy_id=self.params["policy_id"],
            account_id=self.params["account_id"],
        )

    def state_present(self, results):
        condition = self.create_condition_object_based_on_params()
        if not self.live_condition:
            self.api.create_condition(condition)
            results["changed"] = True

        elif condition != self.live_condition:
            condition.id = self.live_condition.id
            condition.guid = self.live_condition.guid
            self.api.update_condition(condition=condition)
            results["changed"] = True
        else:
            condition = self.live_condition

        results["condition"] = condition.output_identity_dict()

    def state_absent(self, results):
        if not self.live_condition:
            return

        results["changed"] = True
        results["condition"] = self.live_condition.output_identity_dict()
        self.api.delete_condition(condition=self.live_condition)

    def create_condition_object_based_on_params(self):
        _cond = NrqlStaticAlertCondition(
            name=self.params["name"],
            account_id=self.params["account_id"],
            policy_id=self.params["policy_id"],
        )
        _cond.enabled = self.params["enabled"]
        _cond.description = self.params["description"]
        _cond.nrql_query = self.params["nrql_query"]
        _cond.runbook_url = self.params["runbook_url"]

        _cond.data_aggregation_window = self.params["data_aggregation_window"]
        _cond.data_slide_by = self.params["data_aggregation_sliding_window"]
        _cond.data_aggregation_method = self.params["data_aggregation_method"]
        if self.params["data_aggregation_method"] == "EVENT_TIMER":
            _cond.data_aggregation_timer = self.params["data_aggregation_timer"]
        else:
            _cond.data_aggregation_delay = self.params["data_aggregation_delay"]

        _cond.evaluation_delay = self.params["evaluation_delay"]
        if self.params["critical_incident"]:
            _cond.incident_terms.append(
                IncidentTerm(
                    priority="CRITICAL",
                    threshold=self.params["critical_incident"]["threshold"],
                    operator=self.params["critical_incident"]["operator"],
                    duration=self.params["critical_incident"]["duration"],
                    occurrences=self.params["critical_incident"]["occurrences"],
                )
            )
        if self.params["warning_incident"]:
            _cond.incident_terms.append(
                IncidentTerm(
                    priority="WARNING",
                    threshold=self.params["warning_incident"]["threshold"],
                    operator=self.params["warning_incident"]["operator"],
                    duration=self.params["warning_incident"]["duration"],
                    occurrences=self.params["warning_incident"]["occurrences"],
                )
            )

        return _cond


def main():
    module_args = {
        **ModuleBase.shared_argument_spec(),
        **dict(
            name=dict(type="str", required=True),
            state=dict(
                type="str",
                choices=["present", "absent"],
                default="present",
                required=False,
            ),
            nrql_query=dict(type="str", required=False),
            policy_id=dict(type="str", required=True),
            runbook_url=dict(type="str", required=False),
            description=dict(type="str", required=False),
            enabled=dict(type="bool", default=True),
            data_aggregation_window=dict(type="int", default=60),
            data_aggregation_sliding_window=dict(type="int", required=False),
            data_aggregation_method=dict(
                type="str",
                default="EVENT_FLOW",
                choices=["EVENT_TIMER", "EVENT_FLOW", "CADENCE"],
            ),
            data_aggregation_delay=dict(type="int", default=120),
            data_aggregation_timer=dict(type="int", default=60),
            evaluation_delay=dict(type="int", required=False),
            critical_incident=dict(
                type="dict",
                required=False,
                options=dict(
                    operator=dict(
                        type="str",
                        required=True,
                        choices=[
                            "ABOVE",
                            "BELOW",
                            "ABOVE_OR_EQUALS",
                            "BELOW_OR_EQUALS",
                            "EQUALS",
                            "NOT_EQUALS",
                        ],
                    ),
                    threshold=dict(type="int", required=True),
                    duration=dict(type="int", default=600),
                    occurrences=dict(
                        type="str", default="ALL", choices=["AT_LEAST_ONCE", "ALL"]
                    ),
                ),
            ),
            warning_incident=dict(
                type="dict",
                required=False,
                options=dict(
                    operator=dict(
                        type="str",
                        required=True,
                        choices=[
                            "ABOVE",
                            "BELOW",
                            "ABOVE_OR_EQUALS",
                            "BELOW_OR_EQUALS",
                            "EQUALS",
                            "NOT_EQUALS",
                        ],
                    ),
                    threshold=dict(type="int", required=True),
                    duration=dict(type="int", default=600),
                    occurrences=dict(
                        type="str", default="ALL", choices=["AT_LEAST_ONCE", "ALL"]
                    ),
                ),
            ),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False, condition={})

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[("state", "present", ("policy_id", "nrql_query"), False)],
    )

    nr_module = NrqlStaticAlertConditionModule(module)
    try:
        nr_module.get_live_condition_from_newrelic()

        if module.params["state"] == "absent":
            nr_module.state_absent(result)

        elif module.params["state"] == "present":
            nr_module.state_present(result)

    except Exception as e:
        nr_module.exit_with_exception(result, e)

    nr_module.exit(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

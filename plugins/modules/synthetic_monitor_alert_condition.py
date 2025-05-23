#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: synthetic_monitor_alert_condition
short_description: Manage a synthetic monitor alert condition
description:
    - Creates, updates, or deletes an alert condition that fires when
      a synthetic monitor fails one or more locations.

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
        default: true
        type: bool
    monitor_guid:
        description:
            - The NR monitor ID from which this condition should pull data
            - This is required when state is present
        required: false
        type: str
    policy_id:
        description:
            - The alert policy ID to which this condition should be added
            - This is required when state is present
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
    data_aggregation_delay:
        description:
            - Delay evaluating the window for this length of time
        required: false
        default: 120
        type: int
    data_aggregation_window:
        description:
            - The length of time that data should be aggregated before evaluation.
            - Windows are opened when an event comes in, rather than on a timer
        required: false
        default: 600
        type: int
    data_aggregation_method:
        description:
            - EVENT_FLOW or EVENT_TIMER
        required: false
        default: EVENT_FLOW
        type: str
    data_aggregation_timer:
        description:
            - The length of time that data should be aggregated before evaluation
            - Timers evaluate signals consistently, instead of waiting for an event to fire
        required: false
        type: int
    critical_incident:
        description:
            - A dictionary describing when a critical incident should be opened
        type: dict
        suboptions:
            failed_locations_threshold:
                description:
                    - The value returned by the NRQL query that triggers an incident
                required: true
                type: int
            duration:
                description:
                    - >-
                      Controls how long the query value needs to be violating the threshold before
                      an incident is created
                default: 600
                type: int
    warning_incident:
        description:
            - A dictionary describing when a warning incident should be opened
        type: dict
        suboptions:
            failed_locations_threshold:
                description:
                    - The value returned by the NRQL query that triggers an incident
                required: true
                type: int
            duration:
                description:
                    - >-
                      Controls how long the query value needs to be violating the threshold before
                      an incident is created
                default: 600
                type: int
"""

EXAMPLES = r"""
- name: Create Synthetic Alert
  newrelic.core.synthetic_monitor_alert_condition:
    name: mmtest
    api_key: "{{ api_key }}"
    account_id: "{{ account_id }}"
    policy_id: "{{ _pol.policy.id }}"
    monitor_guid: "{{ _mon.monitor.guid }}"
    enabled: True
    description: test
    priority: WARNING
    failed_locations_threshold: 2

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
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.objects import (
    NrqlStaticAlertCondition,
    IncidentTerm,
)
from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.api import (
    NrqlAlertConditionApi,
)


logger = logging.getLogger(__name__)


class SyntheticMonitorAlertConditionModule(ModuleBase):
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
        _cond.nrql_query = (
            "SELECT sum(constant) FROM ("
            "SELECT if(latest(result)='FAILED', 1, 0) FROM "
            "SyntheticCheck WHERE entityGuid = '%s' "
            "FACET locationLabel)" % self.params["monitor_guid"]
        )
        _cond.runbook_url = self.params["runbook_url"]
        _cond.data_aggregation_window = self.params["data_aggregation_window"]
        _cond.data_aggregation_method = self.params["data_aggregation_method"]
        _cond.data_aggregation_timer = self.params["data_aggregation_timer"]
        _cond.data_aggregation_delay = self.params["data_aggregation_delay"]
        _cond.signal_slide_by = None
        if self.params["critical_incident"]:
            _cond.incident_terms.append(
                IncidentTerm(
                    priority="CRITICAL",
                    threshold=self.params["critical_incident"][
                        "failed_locations_threshold"
                    ],
                    operator="ABOVE_OR_EQUALS",
                    duration=self.params["critical_incident"]["duration"],
                    occurrences="AT_LEAST_ONCE",
                )
            )
        if self.params["warning_incident"]:
            _cond.incident_terms.append(
                IncidentTerm(
                    priority="WARNING",
                    threshold=self.params["warning_incident"][
                        "failed_locations_threshold"
                    ],
                    operator="ABOVE_OR_EQUALS",
                    duration=self.params["warning_incident"]["duration"],
                    occurrences="AT_LEAST_ONCE",
                )
            )

        return _cond


def main():
    module_args = {
        **ModuleBase.shared_argument_spec(),
        **dict(
            name=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            monitor_guid=dict(type="str", required=False),
            policy_id=dict(type="str", required=True),
            runbook_url=dict(type="str", required=False),
            description=dict(type="str", required=False),
            enabled=dict(type="bool", default=True, required=False),
            data_aggregation_delay=dict(type="int", default=120),
            data_aggregation_window=dict(type="int", default=600),
            data_aggregation_method=dict(type="str", default="EVENT_FLOW"),
            data_aggregation_timer=dict(type="int", required=False),
            critical_incident=dict(
                type="dict",
                required=False,
                options=dict(
                    failed_locations_threshold=dict(type="int", required=True),
                    duration=dict(type="int", default=600),
                ),
            ),
            warning_incident=dict(
                type="dict",
                required=False,
                options=dict(
                    failed_locations_threshold=dict(type="int", required=True),
                    duration=dict(type="int", default=600),
                ),
            ),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False, condition={})

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("monitor_guid", "policy_id"), False),
            ("state", "present", ("critical_incident", "warning_incident"), True),
        ],
    )
    if module.params["description"] is None:
        module.params["description"] = (
            "Alert condition for synthetic monitor %s" % module.params["monitor_guid"]
        )

    smacm = SyntheticMonitorAlertConditionModule(module)
    try:
        smacm.get_live_condition_from_newrelic()

        if module.params["state"] == "absent":
            smacm.state_absent(result)

        elif module.params["state"] == "present":
            smacm.state_present(result)

    except Exception as e:
        smacm.exit_with_exception(result, e)

    smacm.exit(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: alert_condition_info
short_description: Gather info about one or more alert conditions
description: >-
     Gather info about one or more alert conditions

extends_documentation_fragment:
    - newrelic.core.module_base

options:
    name:
        description:
            - The exact name of the synthetic monitor to search for. Mutually exclusive with name_like
        required: false
        type: str
    name_like:
        description:
            - A partial string to search for in alert condition names. Mutually exclusive with name
        required: false
        type: str
    policy_id:
        description:
            - The alert policy ID to which this condition should be added
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Get Alerts That Start With 'Health Check' in Policy _pol.policy.id
  newrelic.core.alert_condition_info:
    name_like: Health Check %
    api_key: "{{ api_key }}"
    account_id: "{{ account_id }}"
    policy_id: "{{ _pol.policy.id }}"
  register: _my_alert_conditions


- name: Get Alerts With The Exact Name 'MY ALERT'
  newrelic.core.synthetic_monitor_alert_condition_info:
    name: MY ALERT
    api_key: "{{ api_key }}"
    account_id: "{{ account_id }}"
  register: _my_alert_conditions


- name: Get All Alerts In A Policy
  newrelic.core.synthetic_monitor_alert_condition_info:
    policy_id: "{{ _pol.policy.id }}"
    api_key: "{{ api_key }}"
    account_id: "{{ account_id }}"
  register: _my_alert_conditions
"""

RETURN = r"""
conditions:
    description:
        - List of conditions matching the search parameters
    type: list
    returned: always
    sample: [
        {
            "id": "22222222",
            "name": "Health Check One is down",
            "policyId": "3333333",
            "type": "STATIC"
        },
        {
            "id": "1111111",
            "name": "Health Check Two is down",
            "policyId": "3333333",
            "type": "STATIC"
        }
    ]
"""

from ansible.module_utils.basic import AnsibleModule

import logging

from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.api import (
    NrqlAlertConditionApi,
)
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)


logger = logging.getLogger(__name__)


class MonitorAlertQueryModule(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = NrqlAlertConditionApi(
            self.params["api_key"],
            self.params["wait_for_propegation"],
            self.params["propegation_timeout"],
        )

    def formulate_query(self):
        if self.params["name_like"]:
            entity_search_query = 'nameLike: "%s"' % self.params["name_like"]
        else:
            entity_search_query = 'name: "%s"' % self.params["name"]

        if self.params["policy_id"]:
            entity_search_query += ', policyId: "%s"' % self.params["policy_id"]

        return entity_search_query

    def run(self, entity_search_query):
        conditions, next_cursor = self.api.get_conditions_from_query(
            entity_search_query, self.params["account_id"]
        )

        while next_cursor:
            _conditions, next_cursor = self.api.get_conditions_from_query(
                entity_search_query, self.params["account_id"]
            )
            conditions += _conditions

        return [c.to_json() for c in conditions]


def main():
    module_args = {
        **ModuleBase.shared_argument_spec(),
        **dict(
            name=dict(type="str", required=False),
            name_like=dict(type="str", required=False),
            policy_id=dict(type="str", default=None, required=False),
        ),
    }

    # seed the result dict in the object
    result = dict(
        changed=False,
        conditions=[],
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[("name", "name_like")],
    )

    maq = MonitorAlertQueryModule(module)
    try:
        result["conditions"] = maq.run(maq.formulate_query())
    except Exception as e:
        maq.exit_with_exception(result, e)

    maq.exit(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

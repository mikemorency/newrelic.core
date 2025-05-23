#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: alert_policy_info
short_description: Lookup an alert policy in New Relic
description: Looks up an alert policy

extends_documentation_fragment:
    - newrelic.core.module_base

options:
    name:
        description:
            - The exact name of the policy to lookup
        required: false
        type: str
    name_like:
        description:
            - A partial name or pattern to use when looking up policies
            - Patterns should be valid NRQL (wildcards are %)
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Lookup a new alert policy
  alert_policy_info:
    name: foo
    api_key: "{{ nr_api_key }}"
    account_id: 1234567

- name: Lookup policies from production
  alert_policy_info:
    name_like: '% production %'
    api_key: "{{ nr_api_key }}"
    account_id: 1234567
"""

RETURN = r"""
policies:
    description:
        - List of dictionaries that describe matching policies
    type: list
    returned: always
    sample: [
        {
            'id': "123456",
            'name': "foo",
            'account_id': "1234",
            'incident_preference': "PREFERENCE"
        }
    ]
"""
from ansible.module_utils.basic import AnsibleModule

import logging
from ansible_collections.newrelic.core.plugins.module_utils.alert_policy.api import (
    AlertPolicyApi,
)
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)


logger = logging.getLogger(__name__)


class AlertPolicyInfoModule(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = AlertPolicyApi(module.params["api_key"])

    def get_policy_by_exact_name(self):
        policy = self.api.get_policy_by_name_and_account(
            name=self.params["name"], account_id=self.params["account_id"]
        )
        return [policy] if policy else []

    def get_policies_by_name_like(self):
        policies, next_cursor = self.api.get_policies_from_query(
            entity_search_query='nameLike: "%s"' % self.params["name_like"],
            account_id=self.params["account_id"],
        )
        while next_cursor:
            _policies, next_cursor = self.api.get_policies_from_query(
                entity_search_query='nameLike: "%s"' % self.params["name_like"],
                account_id=self.params["account_id"],
                cursor=next_cursor,
            )
            policies += _policies
        return policies

    def get_all_policies(self):
        policies, next_cursor = self.api.get_policies_from_query(
            entity_search_query="", account_id=self.params["account_id"]
        )
        while next_cursor:
            _policies, next_cursor = self.api.get_policies_from_query(
                entity_search_query="",
                account_id=self.params["account_id"],
                cursor=next_cursor,
            )
            policies += _policies
        return policies


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = {
        **ModuleBase.shared_argument_spec(),
        **dict(
            name=dict(type="str", required=False),
            name_like=dict(type="str", required=False),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False, policies={})

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[("name", "name_like")],
    )
    apim = AlertPolicyInfoModule(module)

    try:
        if module.params["name"]:
            result["policies"] = apim.get_policy_by_exact_name()
        elif module.params["name_like"]:
            result["policies"] = apim.get_policies_by_name_like()
        else:
            result["policies"] = apim.get_all_policies()
    except Exception as e:
        apim.exit_with_exception(result, e)

    result["policies"] = [p.to_json() for p in result["policies"]]
    apim.exit(result)


def main():
    run_module()


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

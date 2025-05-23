#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: alert_policy
short_description: Manage an alert policy in New Relic
description: Creates, updates, or deletes an alert policy

extends_documentation_fragment:
    - newrelic.core.module_base

options:
    name:
        description:
            - The exact name of the policy to manage
        required: true
        type: str
    state:
        description:
            - Controls if the policy should be 'present' or 'absent'
        required: false
        default: present
        type: str
        choices: ['present', 'absent']
    incident_preference:
        description:
            - The incident preference for the policy and alerts inside
        required: false
        type: str
        default: PER_POLICY
        choices: ['PER_POLICY', 'PER_CONDITION', 'PER_CONDITION_AND_TARGET']
"""

EXAMPLES = r"""
- name: Create a new alert policy
  alert_policy:
    name: foo
    api_key: "{{ nr_api_key }}"
    account_id: 1234567
    incident_preference: PER_CONDITION

- name: Delete an alert policy
  alert_policy:
    name: foo
    api_key: "{{ nr_api_key }}"
    account_id: 1234567
    state: absent
"""

RETURN = r"""
policy:
    description:
        - Identification for the affected policy.
        - Policy ID is only returned if the policy already exists or is created
    type: dict
    returned: always
    sample: {
        'id': "123456",
        'name': "foo",
    }
"""

from ansible.module_utils.basic import AnsibleModule

import logging
from ansible_collections.newrelic.core.plugins.module_utils.alert_policy.objects import (
    AlertPolicy,
)
from ansible_collections.newrelic.core.plugins.module_utils.alert_policy.api import (
    AlertPolicyApi,
)
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)

logger = logging.getLogger(__name__)


class AlertPolicyModule(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = AlertPolicyApi(module.params["api_key"])
        self.live_policy = None

    def get_live_policy_from_newrelic(self):
        """
        This function attempts to lookup the alert policy from New Relic.
        It is not in the init method so we can catch any NR query errors that
        are raised and exit the module with them.
        Returns:
          AlertPolicy or None
        """
        self.live_policy = self.api.get_policy_by_name_and_account(
            name=self.params["name"], account_id=self.params["account_id"]
        )

    def state_present(self, results):
        new_policy = self.create_policy_object_based_on_params()
        if not self.live_policy:
            logger.info("Policy does not exist, it will be created.")
            self.api.create_policy(new_policy)
            results["changed"] = True
            results["policy"]["id"] = new_policy.id
            return

        new_policy.id = self.live_policy.id
        if new_policy == self.live_policy:
            logger.info("Policy exists and matches desired state.")
            results["policy"]["id"] = self.live_policy.id
            return

        logger.info(
            "Policy exists but does not match desired state, it will be updated."
        )
        self.api.update_policy(alert_policy=new_policy)
        results["changed"] = True
        results["policy"]["id"] = new_policy.id

    def state_absent(self, results):
        if not self.live_policy:
            return

        results["changed"] = True
        results["policy"]["id"] = self.live_policy.id
        self.api.delete_policy(alert_policy=self.live_policy)

    def create_policy_object_based_on_params(self):
        policy = AlertPolicy(
            name=self.params["name"],
            account_id=self.params["account_id"],
            incident_preference=self.params["incident_preference"],
        )

        return policy


def main():
    # define available arguments/parameters a user can pass to the module
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
            incident_preference=dict(
                type="str",
                choices=["PER_POLICY", "PER_CONDITION", "PER_CONDITION_AND_TARGET"],
                default="PER_POLICY",
                required=False,
            ),
        ),
    }

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    result = dict(changed=False, policy=dict(name=module.params["name"]))

    apm = AlertPolicyModule(module)
    try:
        apm.get_live_policy_from_newrelic()

        if module.params["state"] == "absent":
            apm.state_absent(result)

        elif module.params["state"] == "present":
            apm.state_present(result)

    except Exception as e:
        apm.exit_with_exception(result, e)

    apm.exit(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

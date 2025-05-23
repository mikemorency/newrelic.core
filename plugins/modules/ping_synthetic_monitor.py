#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: ping_synthetic_monitor
short_description: Manage a synthetic monitor of type ping/simple
description:
    - Creates, updates, or deletes a synthetic monitor of type 'SIMPLE',
      also known as a ping monitor.

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
    period:
        description:
            - The period in which the monitor should be run. Must match the structure defined in the link below
            - https://docs.newrelic.com/docs/apis/nerdgraph/examples/nerdgraph-synthetics-tutorial/#period-attribute
        required: false
        default: EVERY_15_MINUTES
        type: str
        choices: [
            EVERY_MINUTE, EVERY_5_MINUTES, EVERY_10_MINUTES, EVERY_15_MINUTES, EVERY_3O_MINUTES,
            EVERY_HOUR, EVERY_6_HOURS, EVERY_12_HOURS, EVERY_DAY
        ]
    url:
        description:
            - The url that should be monitored
            - This is required when state is present
        required: false
        type: str
    public_locations:
        description:
            - A list of public locations that should run the synthetic check
            - https://docs.newrelic.com/docs/apis/nerdgraph/examples/nerdgraph-synthetics-tutorial/#location-field
            - Either public_locations or private_locations is required when state is present
        required: false
        default: ["AWS_US_WEST_1", "AWS_US_EAST_1", "AWS_US_EAST_2"]
        type: list
        elements: str
    private_locations:
        description:
            - A list of a private location guids that should run the synthetic check
            - Either public_locations or private_locations is required when state is present
        required: false
        default: []
        type: list
        elements: str
    validation_string:
        description:
            - A string to search for in the synthetic response to validate the page loads as expected
            - When not defined, a simple response code check is done (200 is successful)
        required: false
        type: str
    verify_ssl:
        description:
            - If true, SSL will be validated when connecting to the URL
        required: false
        default: false
        type: bool
"""

EXAMPLES = r"""
- name: Create A Monitor
  newrelic.core.ping_synthetic_monitor:
    api_key: "{{ api_key }}"
    account_id: 111111
    name: mon
    period: EVERY_15_MINUTES
    url: "https://example.com"
    enabled: True
    state: present

- name: Delete A Monitor
  newrelic.core.ping_synthetic_monitor:
    api_key: "{{ api_key }}"
    name: mon
    state: absent
"""

RETURN = r"""
monitor:
    description: Dictionary holding monitor identifiers if one was created or updated
    type: dict
    returned: always
    sample: {
        'id': "123345",
        'guid': "ABCDEF12345"
    }
"""
from ansible.module_utils.basic import AnsibleModule

import logging
from ansible_collections.newrelic.core.plugins.module_utils.synthetic.api import (
    SyntheticMonitorApi,
)
from ansible_collections.newrelic.core.plugins.module_utils.synthetic.objects import (
    PingSyntheticMonitor,
)
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)


logger = logging.getLogger(__name__)


class PingSyntheticMonitorModule(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = SyntheticMonitorApi(
            self.params["api_key"],
            self.params["wait_for_propegation"],
            self.params["propegation_timeout"],
        )
        self.live_monitor = None

    def get_live_monitor_from_newrelic(self):
        """
        This function attempts to lookup the synthetic monitor from New Relic.
        It is not in the init method so we can catch any NR query errors that
        are raised and exit the module with them.
        Returns:
          SyntheticMonitor or None
        """
        self.live_monitor = self.api.get_monitor_by_name_and_account(
            name=self.params["name"], account_id=self.params["account_id"]
        )

    def state_present(self, results):
        new_monitor = self.create_monitor_object_based_on_params()
        if not self.live_monitor:
            logger.info("Monitor does not exist, it will be created.")
            self.api.create_monitor(new_monitor)
            results["changed"] = True
            results["monitor"] = new_monitor.to_json()
            return

        new_monitor.id = self.live_monitor.id
        new_monitor.guid = self.live_monitor.guid
        if new_monitor == self.live_monitor:
            logger.info("Monitor exists and matches desired state.")
            results["monitor"] = self.live_monitor.to_json()
            return

        logger.info(
            "Monitor exists but does not match desired state, it will be updated."
        )
        self.api.update_monitor(monitor=new_monitor)
        results["changed"] = True
        results["monitor"] = new_monitor.to_json()

    def state_absent(self, results):
        if not self.live_monitor:
            return

        results["changed"] = True
        results["monitor"] = {"id": self.live_monitor.id}
        self.api.delete_monitor(monitor=self.live_monitor)

    def create_monitor_object_based_on_params(self):
        monitor = PingSyntheticMonitor(
            name=self.params["name"], account_id=self.params["account_id"]
        )
        monitor.url = self.params["url"]
        monitor.private_locations = self.params["private_locations"]
        monitor.public_locations = self.params["public_locations"]
        monitor.period = self.params["period"]
        monitor.enabled = self.params["enabled"]
        monitor.validation_string = self.params["validation_string"]
        monitor.verify_ssl = self.params["verify_ssl"]

        return monitor


def run_module():
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
            url=dict(type="str", default=None, required=False),
            period=dict(
                type="str",
                default="EVERY_15_MINUTES",
                required=False,
                choices=[
                    "EVERY_MINUTE",
                    "EVERY_5_MINUTES",
                    "EVERY_10_MINUTES",
                    "EVERY_15_MINUTES",
                    "EVERY_3O_MINUTES",
                    "EVERY_HOUR",
                    "EVERY_6_HOURS",
                    "EVERY_12_HOURS",
                    "EVERY_DAY",
                ],
            ),
            public_locations=dict(
                type="list",
                default=["AWS_US_WEST_1", "AWS_US_EAST_1", "AWS_US_EAST_2"],
                required=False,
                elements="str",
            ),
            private_locations=dict(
                type="list", default=[], required=False, elements="str"
            ),
            enabled=dict(type="bool", default=True, required=False),
            validation_string=dict(type="str", default=None, required=False),
            verify_ssl=dict(type="bool", default=False, required=False),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    psmmm = PingSyntheticMonitorModule(module)
    try:
        psmmm.get_live_monitor_from_newrelic()

        if module.params["state"] == "absent":
            psmmm.state_absent(result)

        elif module.params["state"] == "present":
            psmmm.state_present(result)

    except Exception as e:
        psmmm.exit_with_exception(result, e)

    psmmm.exit(result)


def main():
    run_module()


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

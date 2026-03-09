#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: cert_synthetic_monitor
short_description: Manage a synthetic monitor of type certificate check
description:
    - Creates, updates, or deletes a synthetic monitor of type 'CERT_CHECK',
      also known as a certificate check monitor.

extends_documentation_fragment:
    - newrelic.core.module_base
    - newrelic.core.synthetic_monitors

options:
    domain:
        description:
            - The domain that should be monitored. This should not include the protocol (http/https)
            - This is required when state is present
        required: false
        type: str
        aliases: [url]
    days_before_cert_expires_to_trigger_failure:
        description:
            - The number of days before the certificate expires that the monitor should trigger a failure
            - For example, if you set this to 30, the monitor will trigger a failure if the certificate expires in the next 30 days
            - Required when state is present
        required: false
        default: 30
        type: int
"""

EXAMPLES = r"""
- name: Create A Monitor
  newrelic.core.cert_synthetic_monitor:
    api_key: "{{ api_key }}"
    account_id: 111111
    name: mon
    period: EVERY_15_MINUTES
    domain: "example.com"
    enabled: True
    state: present
    days_before_cert_expires_to_trigger_failure: 30

- name: Delete A Monitor
  newrelic.core.cert_synthetic_monitor:
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
from ansible_collections.newrelic.core.plugins.module_utils.api.synthetic import (
    SyntheticMonitorApi,
)
from ansible_collections.newrelic.core.plugins.module_utils.models.synthetic import (
    CertSyntheticMonitor,
    MonitorPeriod,
)
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)


logger = logging.getLogger(__name__)


class CertSyntheticMonitorModule(ModuleBase):
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
        monitor = CertSyntheticMonitor(
            name=self.params["name"], account_id=self.params["account_id"]
        )
        monitor.url = self.params["domain"]
        monitor.private_locations = self.params["private_locations"]
        monitor.public_locations = self.params["public_locations"]
        monitor.period = MonitorPeriod[self.params["period"]]
        monitor.enabled = self.params["enabled"]
        monitor.days_before_cert_expires_to_trigger_failure = self.params[
            "days_before_cert_expires_to_trigger_failure"
        ]

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
            domain=dict(type="str", default=None, required=False, aliases=["url"]),
            period=dict(
                type="str",
                default="EVERY_15_MINUTES",
                required=False,
                choices=[e.name for e in MonitorPeriod],
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
            days_before_cert_expires_to_trigger_failure=dict(
                type="int", default=30, required=False
            ),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    smmm = CertSyntheticMonitorModule(module)
    try:
        smmm.get_live_monitor_from_newrelic()

        if module.params["state"] == "absent":
            smmm.state_absent(result)

        elif module.params["state"] == "present":
            smmm.state_present(result)

    except Exception as e:
        smmm.exit_with_exception(result, e)

    smmm.exit(result)


def main():
    run_module()


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

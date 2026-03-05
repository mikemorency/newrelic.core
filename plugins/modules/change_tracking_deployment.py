#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: change_tracking_deployment
short_description: Create a deployment event in New Relic's Change Tracking for a givenlist of entities
description:
    - Creates a deployment event in New Relic's Change Tracking. Events can be associated with any types of entities.
    - This module will create an event each time it is run, even if the version already exists.
      Idempotency support may be added in the future, pending New Relic's API endpoints.
    - If you want to create a deployment event for multiple entities, you can supply multiple entity guids. The events
      that are created will have unique IDs and be treated as separate events. See the group_id option for associating events
      together.

extends_documentation_fragment:
    - newrelic.core.change_tracking

options:
    version:
        description:
            - The version of the deployment to track
            - This does not need to be unique. A new event will be created even if the version already exists
        required: true
        type: str

    user:
        description:
            - The user to associate with the deployment event
            - This does not need to be a valid New Relic user. It can be any string.
        required: false
        type: str
    group_id:
        description:
            - The group id to associate with the deployment event.
            - Groups can be used to associate a series of changes to one or more entities, or releasing many changes across many entities within your system.
            - By setting the same group_id value for related deployments, you can more easily see these changes together in New Relic interfaces or use the
              group_id to narrow query results.
            - This can be any string of your choosing and you can continue to add deployments to a group after the first use of the group_id
              (in case you want to relate this deployment to one that happened weeks or even months ago).
            - For example, you can group deployments by a common attribute, such as a release or environment.
        required: false
        type: str
    changelog:
        description:
            - A url or string to indicate a changelog for the deployment.
        required: false
        type: str
    description:
        description:
            - A string used to describe the deployment.
        required: false
        type: str
    commit:
        description:
            - A string to indicate the commit hash of the deployment
        required: false
        type: str
    deep_link:
        description:
            - An arbitrary URL to associate with the deployment.
            - This could be a link to the CI source for example.
        required: false
        type: str
    deployment_type:
        description:
            - The type of deployment.
            - This attribute is used to categorize and filter deployments in the New Relic UI.
        required: false
        type: str
        choices: [BASIC, BLUE_GREEN, CANARY, ROLLING, SHADOW, OTHER]
    timestamp:
        description:
            - The exact time of the deployment.
            - This value must be within plus/minus 24 hours from the current time. This is a New Relic requirement.
            - If no timestamp is provided, the current time will be used.
        type: str
"""

EXAMPLES = r"""
- name: Create A Deployment Event
  newrelic.core.change_tracking_deployment:
    api_key: "{{ api_key }}"
    version: "1.0.0"
    entity_guids:
      - '111111111-111111111-1111111'
    user: "ansible"
    group_id: "production-group-1"
    changelog: "https://example.com/changelog"
    description: "Deployed version 1.0.0"
    commit: "1234567890"
    deep_link: "https://example.com/ci"
    deployment_type: "ROLLING"
    timestamp: "2024-01-01T00:00:00Z"
"""

RETURN = r"""
events:
    description:
      - Dictionary holding the deployment event identifiers if one was created or updated
      - Keys correspond to entity guids and values correspond to the event IDs
    type: dict
    returned: always
    sample: {
        '111111111-111111111-1111111': "123345"
    }
"""

from ansible.module_utils.basic import AnsibleModule
import logging

from ansible_collections.newrelic.core.plugins.module_utils.api.change_tracking import (
    ChangeTrackingDeploymentApi,
)
from ansible_collections.newrelic.core.plugins.module_utils.models.change_tracking import (
    DeploymentEvent,
)
from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ChangeTrackingModuleBase,
)


logger = logging.getLogger(__name__)


class ChangeTrackingDeploymentModule(ChangeTrackingModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = ChangeTrackingDeploymentApi(self.params["api_key"])

    def create_event_object_based_on_params(self, entity_guid: str):
        event = DeploymentEvent(
            entity_guid=entity_guid,
            version=self.params["version"],
            timestamp=self.params["timestamp"],
        )
        event.changelog = self.params["changelog"]
        event.commit = self.params["commit"]
        event.deep_link = self.params["deep_link"]
        event.deployment_type = self.params["deployment_type"]
        event.description = self.params["description"]
        event.group_id = self.params["group_id"]
        event.user = self.params["user"]

        return event

    def state_present(self, results):
        new_events = list()
        for entity_guid in self.params["entity_guids"]:
            new_events.append(self.create_event_object_based_on_params(entity_guid))

        if new_events:
            logger.info("Events do not exist, they will be created.")
            self.api.create_deployment_events(new_events)
            results["changed"] = True
            results["events"] = {
                new_event.entity_guid: new_event.id for new_event in new_events
            }
            return


def run_module():
    module_args = {
        **ChangeTrackingModuleBase.shared_argument_spec(),
        **dict(
            version=dict(type="str", required=True),
            user=dict(type="str", required=False),
            changelog=dict(type="str", required=False),
            commit=dict(type="str", required=False),
            deep_link=dict(type="str", required=False),
            deployment_type=dict(
                type="str",
                required=False,
                choices=["BASIC", "BLUE_GREEN", "CANARY", "ROLLING", "SHADOW", "OTHER"],
            ),
            group_id=dict(type="str", required=False),
            description=dict(type="str", required=False),
            timestamp=dict(type="str", required=False)
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False, events=dict())

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    chtde = ChangeTrackingDeploymentModule(module)
    try:
        chtde.state_present(result)

    except Exception as e:
        chtde.exit_with_exception(result, e)

    chtde.exit(result)


def main():
    run_module()


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

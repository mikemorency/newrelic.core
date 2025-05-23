#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: entity_info
short_description: Manages tags on a New Relic entity
description:
    - Manages the tags on a New Relic entity.
    - You can overwrite tags, append new tags, or remove tags all together.

extends_documentation_fragment:
    - newrelic.core.module_base

options:
    guid:
        description:
            - The GUID of the entity to manage
        required: true
        type: str
"""

EXAMPLES = r"""
- name: Gather Entity Info
  newrelic.info.entity_info:
    api_key: NRAK-11111111111111111111111
    guid: 222222-222222222-2222222222-222222222
    account_id: 111111
"""

RETURN = r"""
guid:
    description: The entity GUID
    type: str
    returned: on success
    sample: 123456
name:
    description: The entity name
    type: str
    returned: on success
    sample: some-name
changed_tags:
    description: Dictionary of tags that are changed. Includes their new and old values
    type: dict
    returned: on success
    sample: {
        "example": {
            "new_values": [
                "2",
                "1",
                "buzz",
                "bizz"
            ],
            "old_values": [
                "1",
                "buzz",
                "2"
            ]
        }
    }
"""
from ansible.module_utils.basic import AnsibleModule

import logging

from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.entity.api import EntityApi


logger = logging.getLogger(__name__)


class EntityInfo(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = EntityApi(
            self.params["api_key"],
            self.params["wait_for_propegation"],
            self.params["propegation_timeout"],
        )
        self.entity = self.api.get_entity_by_guid(self.params["guid"])


def main():
    module_args = {
        **ModuleBase.shared_argument_spec(),
        **dict(
            guid=dict(type="str", required=True),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    nr_module = EntityInfo(module)
    try:
        result["entities"] = [nr_module.entity.to_json()]

    except Exception as e:
        nr_module.exit_with_exception(result, e)

    nr_module.exit(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

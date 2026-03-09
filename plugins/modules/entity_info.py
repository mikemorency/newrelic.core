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
short_description: Gathers information about one or more entities
description:
    - Gathers information about one or more entities in New Relic.
    - Allows you to search by guid or by NRQL query

extends_documentation_fragment:
    - newrelic.core.module_base

options:
    guid:
        description:
            - The GUID of the entity for which to search
            - guid and query are mutually exclusive
        required: false
        type: str
    query:
        description:
            - The NRQL query to use when searching for entities
            - guid and query are mutually exclusive
        required: false
        type: str
"""

EXAMPLES = r"""
- name: Gather info about a single entity
  newrelic.core.entity_info:
    api_key: NRAK-11111111111111111111111
    guid: 222222-222222222-2222222222-222222222
    account_id: 111111

- name: Query for multiple entities
  newrelic.core.entity_info:
    api_key: NRAK-11111111111111111111111
    query: name LIKE 'my-monitors'
    account_id: 111111
"""

RETURN = r"""
entities:
    description: A list of entities that matched the searched parameters
    type: list
    returned: always
    sample: [
    ]
"""
from ansible.module_utils.basic import AnsibleModule

import logging

from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.api.entity import EntityApi


logger = logging.getLogger(__name__)


class EntityInfo(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.account_id = self.params["account_id"]
        self.api = EntityApi(
            self.params["api_key"],
            self.params["wait_for_propegation"],
            self.params["propegation_timeout"],
        )

    def get_entities(self):
        if self.params["guid"]:
            entity = self.api.get_entity_by_guid_and_account_id(
                guid=self.params["guid"], account_id=self.account_id
            )
            return [entity] if entity else []

        query_param = self.params["query"]
        if not query_param:
            query = f"accountId = '{self.account_id}'"
        elif "accountId" not in query_param:
            query = f"{query_param} AND accountId = '{self.account_id}'"
        else:
            query = query_param

        return self.api.get_entities_by_search_query(entity_search_query=query)


def main():
    module_args = {
        **ModuleBase.shared_argument_spec(),
        **dict(
            guid=dict(type="str", required=False),
            query=dict(type="str", required=False),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[("guid", "query")],
    )

    nr_module = EntityInfo(module)
    try:
        entities = nr_module.get_entities()
        result["entities"] = [entity.to_json() for entity in entities]

    except Exception as e:
        nr_module.exit_with_exception(result, e)

    nr_module.exit(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, mikemorency
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: entity_tags
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
    tags:
        description:
            - A dictionary of keys and values that should be added as tags to the entity
            - New Relic requires unique keys with a list of values. Each key value pair is then
              added to the entity. So an input of {"foo":["one","two"]} will become {"foo":"one"}
              and {"foo":"two"} on the entity.
        required: true
        type: dict
    state:
        description:
            - If the tags should be added or removed from the entity.
            - If state is absent and values are provided, only those values with the provided key are removed.
            - If state is absent and values are not provided, any values with the provided key are removed.
            - If state is present, tags with the provided keys and values are added to the entity.
        type: str
        choices: [present, absent]
        default: present
    append:
        description:
            - If true, tag values will be appended to existing tag values with the same key.
            - If false, tag values will replace existing tag values with the same key.
        default: true
        type: bool
"""

EXAMPLES = r"""
- name: Get Info
  newrelic.info.alert_condition_info:
    api_key: NRAK-11111111111111111111111
    name: some_alert_condition
    account_id: 111111
  register: _condition

- name: Add Tags (If Missing) To Existing Set
  newrelic.info.entity_tags:
    api_key: NRAK-11111111111111111111111
    guid: "{{ _condition.conditions[0].guid }}"
    state: present
    tags:
      mmtest: [bizz, buzz, 1, 2]

- name: Overwrite Tags With The Same Key
  newrelic.info.entity_tags:
    api_key: NRAK-11111111111111111111111
    guid: "{{ _condition.conditions[0].guid }}"
    append: false
    tags:
      mmtest: [bizz, buzz]

- name: Remove Tag example:True
  newrelic.info.entity_tags:
    api_key: NRAK-111111111111111111111111
    guid: "{{ _condition.conditions[0].guid }}"
    tags:
      example: [True]
    state: absent

- name: Remove All Tags With Key example
  newrelic.info.entity_tags:
    api_key: NRAK-111111111111111111111111
    guid: "{{ _condition.conditions[0].guid }}"
    state: absent
    tags:
      example: []
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
import time

from ansible_collections.newrelic.core.plugins.module_utils.module_base import (
    ModuleBase,
)
from ansible_collections.newrelic.core.plugins.module_utils.entity.api import EntityApi
from ansible_collections.newrelic.core.plugins.module_utils.entity.query_templates import (
    EntityQueryTemplates,
)
from ansible_collections.newrelic.core.plugins.module_utils.entity.objects import (
    EntityTags,
)

logger = logging.getLogger(__name__)


class EntityTagModule(ModuleBase):
    def __init__(self, module):
        super().__init__(module)
        self.api = EntityApi(
            self.params["api_key"],
            self.params["wait_for_propegation"],
            self.params["propegation_timeout"],
        )
        self.entity = self.api.get_entity_by_guid(self.params["guid"])
        self.param_tags = EntityTags(self.params["tags"])

    def get_tags_to_remove(self):
        logging.info("Calculating the tags the need keys or values removed.")
        removed_keys = EntityTags()
        removed_values = EntityTags()
        for tag in self.param_tags:
            if not self.entity.tags.contains_tag(tag):
                continue

            if tag.values:
                removed = self.entity.tags.remove_values(tag)
                if removed:
                    removed_values.add_tag(removed)
            else:
                removed = self.entity.tags.remove_key(tag.name)
                if removed:
                    removed_keys.add_tag(removed)

        logging.info("The following tag keys will be removed: %s", removed_keys)
        logging.info("The following tag values will be removed: %s", removed_values)
        return removed_keys, removed_values

    def get_tags_to_add_or_update(self):
        tags_to_update = EntityTags()
        tags_to_replace = EntityTags()
        for param_tag in self.param_tags:
            if self.params["append"]:
                new_tag = self.entity.tags.add_tag(param_tag)
                if new_tag:
                    logger.debug("Tag %s will be updated", new_tag.name)
                    tags_to_update.add_tag(new_tag)
            else:
                new_tag = self.entity.tags.replace_tag(param_tag)
                if new_tag:
                    logger.debug("Tag %s will be replaced", new_tag.name)
                    tags_to_replace.add_tag(new_tag)

        logging.info("The following tags need to be updated: %s", tags_to_update)
        logging.info("The following tags need to be replaced: %s", tags_to_replace)
        return tags_to_update, tags_to_replace

    def add_tags(self, tag_changes: tuple):
        tags_to_update = tag_changes[0]
        tags_to_replace = tag_changes[1]
        if not self.params["append"]:
            self.remove_tags((tags_to_replace, []))
        query_template = self.api.jinja_env.from_string(
            EntityQueryTemplates.j2_add_or_update_tags()
        )
        query = query_template.render(
            guid=self.entity.guid, tags=tags_to_update.merge(tags_to_replace)
        )
        self.__run_query_with_error_catch(
            query=query, error_key="taggingAddTagsToEntity"
        )

    def remove_tags(self, tag_changes: tuple):
        removed_values = tag_changes[1]
        removed_key_names = [t.name for t in tag_changes[0]]

        if removed_key_names:
            logger.info(
                "Removing any tags with the following keys from entity: %s.",
                removed_key_names,
            )
            query_template = self.api.jinja_env.from_string(
                EntityQueryTemplates.j2_remove_tags_by_keys()
            )
            query = query_template.render(
                guid=self.entity.guid, tag_names=removed_key_names
            )
            self.__run_query_with_error_catch(
                query=query, error_key="taggingDeleteTagFromEntity"
            )

        if len(removed_values) > 0:
            logger.info("Removing specific values from entity: %s.", removed_values)
            query_template = self.api.jinja_env.from_string(
                EntityQueryTemplates.j2_remove_tag_values()
            )
            query = query_template.render(guid=self.entity.guid, tags=removed_values)
            self.__run_query_with_error_catch(
                query=query, error_key="taggingDeleteTagValuesFromEntity"
            )

    def __run_query_with_error_catch(self, query, error_key):
        logger.debug("query=%s", "".join(query.split()))
        r = self.api.run_query(query=query)
        try:
            errors = r["data"][error_key]["errors"]
        except KeyError as e:
            logger.fatal("Encountered key error on '%s'", e)
            logger.fatal("response=%s", r)
            raise Exception("Query response did not match excepted format")

        if errors:
            raise Exception(errors)

    def _wait_for_tag_changes(self, changed: EntityTags):
        """
        Changes take time to propagate in NR, so this will wait until the
        change can be seen in the API before continuing.
        At the end of the loop there's another small pause, since the change may only be
        partially propagated but we can't really check any further.
        """
        _time_increment = 3
        if not self.api.wait_for_propegation:
            return
        _time = 0
        while _time < self.api.propegation_timeout:
            time.sleep(_time_increment)
            _time += _time_increment
            remote_entity_def = self.api.get_entity_by_guid(self.params["guid"])
            for tag in changed:
                if (
                    remote_entity_def.tags.contains_tag(tag)
                    and self.params["state"] == "absent"
                ) or (
                    not remote_entity_def.tags.contains_tag(tag)
                    and self.params["state"] == "present"
                ):
                    break
            else:
                break
        else:
            raise Exception(
                "Timedout waiting for new tags to be shown in New Relic API"
            )

        # wait one more time because the nr api really does mess with you sometimes
        time.sleep(_time_increment)


def main():
    module_args = {
        **ModuleBase.shared_argument_spec(),
        **dict(
            append=dict(type="bool", default=True),
            guid=dict(type="str", required=True),
            tags=dict(type="dict", required=True),
            state=dict(type="str", choices=["absent", "present"], default="present"),
        ),
    }

    # seed the result dict in the object
    result = dict(changed=False)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    nr_module = EntityTagModule(module)
    try:
        result["name"] = nr_module.entity.name
        result["guid"] = nr_module.entity.guid

        if module.params["state"] == "present":
            tag_changes = nr_module.get_tags_to_add_or_update()
        else:
            tag_changes = nr_module.get_tags_to_remove()

        all_changes = tag_changes[0].merge(tag_changes[1])
        result["changed_tags"] = all_changes.to_json()
        if result["changed_tags"]:
            result["changed"] = True
            if module.params["state"] == "absent":
                nr_module.remove_tags(tag_changes)
            else:
                nr_module.add_tags(tag_changes)
            nr_module._wait_for_tag_changes(all_changes)

    except Exception as e:
        nr_module.exit_with_exception(result, e)

    nr_module.exit(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()

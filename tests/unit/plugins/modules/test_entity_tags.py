from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ...common.utils import run_module, ModuleTestCase

from ansible_collections.newrelic.core.plugins.module_utils.entity.objects import (
    Entity,
    EntityTags,
)

from ansible_collections.newrelic.core.plugins.modules.entity_tags import (
    main as module_main,
)


class TestNrModule(ModuleTestCase):
    def __prepare(self, mocker):
        self.api_class = (
            "ansible_collections.newrelic.core.plugins.modules.entity_tags.EntityApi"
        )
        self.default_args = dict(guid="123", tags=dict(one=[1, 11], two=[2]))
        self.test_entity = Entity(
            name="foo",
            account_id="",
            guid=self.default_args["guid"],
        )
        self.test_entity.tags = EntityTags(self.default_args["tags"])

        mocker.patch(
            self.api_class + ".get_entity_by_guid", return_value=self.test_entity
        )

    def test_absent(self, mocker):
        self.__prepare(mocker)

        # no difference
        module_args = {
            **self.default_args,
            **dict(state="absent", tags=dict(three=["3"])),
        }
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is False

        # remove tag by key
        mocker.patch(
            self.api_class + ".run_query",
            return_value={"data": {"taggingDeleteTagFromEntity": {"errors": []}}},
        )
        module_args = {**self.default_args, **dict(state="absent", tags=dict(one=[]))}
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is True
        assert set(result["changed_tags"]["one"]) == set(["1", "11"])

        # remove tag by values
        mocker.patch(
            self.api_class + ".run_query",
            return_value={"data": {"taggingDeleteTagValuesFromEntity": {"errors": []}}},
        )

        self.test_entity.tags = EntityTags(self.default_args["tags"])
        module_args = {**self.default_args, **dict(state="absent", tags=dict(one=[1]))}
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is True
        assert set(result["changed_tags"]["one"]) == set(["1"])

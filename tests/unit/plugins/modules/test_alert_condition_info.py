from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ...common.utils import run_module, ModuleTestCase

from ansible_collections.newrelic.core.plugins.modules.alert_condition_info import (
    main as module_main,
)

from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.objects import (
    NrqlAlertConditionBase,
)


class TestNrModule(ModuleTestCase):
    def __prepare(self, mocker):
        self.mock_api = mocker.Mock()
        mocker.patch(
            "ansible_collections.newrelic.core.plugins.modules.alert_condition_info.NrqlAlertConditionApi.__new__",
            return_value=self.mock_api,
        )

    def test_no_name_input(self, mocker):
        self.__prepare(mocker)
        conditions = [
            NrqlAlertConditionBase(name="1", account_id="1234"),
            NrqlAlertConditionBase(name="2", account_id="1234"),
        ]
        self.mock_api.get_conditions_from_query.return_value = (conditions, None)
        result = run_module(module_entry=module_main, module_args=dict())

        assert result["changed"] is False
        assert result["conditions"] == [c.to_json() for c in conditions]

        self.mock_api.get_conditions_from_query.return_value = ([], None)
        result = run_module(module_entry=module_main, module_args=dict(policy_id="1"))

        assert result["changed"] is False
        assert result["conditions"] == []

    def test_name(self, mocker):
        self.__prepare(mocker)
        conditions = [NrqlAlertConditionBase(name="1", account_id="1234")]
        self.mock_api.get_conditions_from_query.return_value = (conditions, None)
        result = run_module(module_entry=module_main, module_args=dict(name="1"))

        assert result["changed"] is False
        assert result["conditions"] == [conditions[0].to_json()]

    def test_name_like(self, mocker):
        self.__prepare(mocker)
        conditions = [
            NrqlAlertConditionBase(name="1", account_id="1234"),
            NrqlAlertConditionBase(name="12", account_id="1234"),
        ]
        self.mock_api.get_conditions_from_query.side_effect = [
            ([conditions[0]], 1),
            ([conditions[1]], None),
        ]
        result = run_module(module_entry=module_main, module_args=dict(name_like="1"))

        assert self.mock_api.get_conditions_from_query.call_count == 2
        assert result["changed"] is False
        assert result["conditions"] == [c.to_json() for c in conditions]

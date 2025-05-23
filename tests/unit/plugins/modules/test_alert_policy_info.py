from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ...common.utils import run_module, ModuleTestCase

from ansible_collections.newrelic.core.plugins.modules.alert_policy_info import (
    main as module_main,
)

from ansible_collections.newrelic.core.plugins.module_utils.alert_policy.objects import (
    AlertPolicy,
)


class TestNrModule(ModuleTestCase):
    def __prepare(self, mocker):
        self.mock_api = mocker.Mock()
        mocker.patch(
            "ansible_collections.newrelic.core.plugins.modules.alert_policy_info.AlertPolicyApi.__new__",
            return_value=self.mock_api,
        )

    def test_no_name_input(self, mocker):
        self.__prepare(mocker)
        policies = [
            AlertPolicy(name="1", incident_preference="", account_id="1234"),
            AlertPolicy(name="2", incident_preference="", account_id="1234"),
        ]
        self.mock_api.get_policies_from_query.return_value = (policies, None)
        result = run_module(module_entry=module_main, module_args=dict())

        assert result["changed"] is False
        assert result["policies"] == [p.to_json() for p in policies]

        self.mock_api.get_policies_from_query.return_value = ([], None)
        result = run_module(module_entry=module_main, module_args=dict())

        assert result["changed"] is False
        assert result["policies"] == []

    def test_name(self, mocker):
        self.__prepare(mocker)
        policy = AlertPolicy(name="1", incident_preference="", account_id="1234")
        self.mock_api.get_policy_by_name_and_account.return_value = policy
        result = run_module(module_entry=module_main, module_args=dict(name="1"))

        assert result["changed"] is False
        assert result["policies"] == [policy.to_json()]

    def test_name_like(self, mocker):
        self.__prepare(mocker)
        policies = [
            AlertPolicy(name="1", incident_preference="", account_id="1234"),
            AlertPolicy(name="12", incident_preference="", account_id="1234"),
        ]
        self.mock_api.get_policies_from_query.side_effect = [
            ([policies[0]], 1),
            ([policies[1]], None),
        ]
        result = run_module(module_entry=module_main, module_args=dict(name_like="1"))

        assert self.mock_api.get_policies_from_query.call_count == 2
        assert result["changed"] is False
        assert result["policies"] == [p.to_json() for p in policies]

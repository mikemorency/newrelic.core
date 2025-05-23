from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ...common.utils import run_module, ModuleTestCase

from ansible_collections.newrelic.core.plugins.modules.alert_policy import (
    main as module_main,
)

from ansible_collections.newrelic.core.plugins.module_utils.alert_policy.objects import (
    AlertPolicy,
)


class TestNrModule(ModuleTestCase):
    def __prepare(self, mocker):
        self.mock_api = mocker.Mock()
        self.default_args = dict(name="foo", account_id="1234")
        self.test_policy = AlertPolicy(
            name=self.default_args["name"],
            incident_preference="PER_POLICY",
            account_id=self.default_args["account_id"],
        )
        mocker.patch(
            "ansible_collections.newrelic.core.plugins.modules.alert_policy.AlertPolicyApi.__new__",
            return_value=self.mock_api,
        )

    def test_absent(self, mocker):
        self.__prepare(mocker)
        self.test_policy.id = 1
        module_args = {**self.default_args, **dict(state="absent")}
        # no policy
        self.mock_api.get_policy_by_name_and_account.return_value = None
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is False

        # policy
        self.mock_api.get_policy_by_name_and_account.return_value = self.test_policy
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is True
        assert result["policy"]["id"] == 1

    def test_present_create(self, mocker):
        def set_policy_id(policy):
            policy.id = 1

        self.__prepare(mocker)
        self.mock_api.get_policy_by_name_and_account.return_value = None
        self.mock_api.create_policy.side_effect = set_policy_id
        result = run_module(module_entry=module_main, module_args=self.default_args)

        self.mock_api.create_policy.assert_called_once()
        assert result["changed"] is True
        assert result["policy"]["id"] == 1

    def test_present_no_change(self, mocker):
        self.__prepare(mocker)
        self.test_policy.id = 1
        self.mock_api.get_policy_by_name_and_account.return_value = self.test_policy
        result = run_module(module_entry=module_main, module_args=self.default_args)

        assert result["changed"] is False
        assert result["policy"]["id"] == 1

    def test_present_update(self, mocker):
        self.__prepare(mocker)
        self.test_policy.id = 1
        module_args = {**self.default_args, **dict(incident_preference="PER_CONDITION")}
        self.mock_api.get_policy_by_name_and_account.return_value = self.test_policy
        result = run_module(module_entry=module_main, module_args=module_args)

        self.mock_api.update_policy.assert_called_once()
        assert result["changed"] is True
        assert result["policy"]["id"] == 1

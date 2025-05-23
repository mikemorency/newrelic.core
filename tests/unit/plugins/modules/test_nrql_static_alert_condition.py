from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ...common.utils import run_module, ModuleTestCase

from ansible_collections.newrelic.core.plugins.modules.nrql_static_alert_condition import (
    main as module_main,
)
from ansible_collections.newrelic.core.plugins.module_utils.alert_condition.objects import (
    NrqlStaticAlertCondition,
    IncidentTerm,
)


class TestNrModule(ModuleTestCase):
    def __prepare(self, mocker):
        self.api_class = "ansible_collections.newrelic.core.plugins.modules.nrql_static_alert_condition.NrqlAlertConditionApi"
        self.default_args = dict(
            name="foo",
            account_id="1234",
            nrql_query="foo",
            policy_id="123",
            runbook_url="a",
            description="a",
            data_aggregation_window=1,
            data_aggregation_delay=1,
            data_aggregation_method="EVENT_FLOW",
            critical_incident=dict(
                operator="BELOW", threshold=1, duration=2, occurrences="ALL"
            ),
            warning_incident=dict(
                operator="ABOVE", threshold=1, duration=2, occurrences="ALL"
            ),
        )
        self.test_condition = NrqlStaticAlertCondition(
            name=self.default_args["name"],
            account_id=self.default_args["account_id"],
            policy_id=self.default_args["policy_id"],
        )
        for k, v in self.default_args.items():
            if k.endswith("incident"):
                self.test_condition.incident_terms.append(
                    IncidentTerm(**v, priority=k.split("_", maxsplit=1)[0].upper())
                )
            else:
                setattr(self.test_condition, k, v)

    def test_absent(self, mocker):
        self.__prepare(mocker)
        module_args = dict(name="foo", policy_id="123", state="absent")

        # no difference
        mocker.patch(
            self.api_class + ".get_condition_by_name_policy_and_account",
            return_value=None,
        )
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is False

        # remove condition
        mocker.patch(
            self.api_class + ".get_condition_by_name_policy_and_account",
            return_value=self.test_condition,
        )
        del_mock = mocker.patch(self.api_class + ".delete_condition")
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is True
        del_mock.assert_called_once()

    def test_create(self, mocker):
        self.__prepare(mocker)
        mocker.patch(
            self.api_class + ".get_condition_by_name_policy_and_account",
            return_value=None,
        )
        mocker.patch(
            self.api_class + ".run_query",
            return_value={
                "data": {"alertsNrqlConditionStaticCreate": {"id": 1, "entityGuid": 2}}
            },
        )
        result = run_module(module_entry=module_main, module_args=self.default_args)

        assert result["changed"] is True
        assert result["condition"]["id"] == 1

    def _update_desc_side_effect(self, **kwargs):
        self.test_condition.description = "b"
        return {"data": {"alertsNrqlConditionStaticUpdate": {"id": 1, "entityGuid": 2}}}

    def test_update(self, mocker):
        self.__prepare(mocker)
        mocker.patch(
            self.api_class + ".get_condition_by_name_policy_and_account",
            return_value=self.test_condition,
        )
        # test no change
        result = run_module(module_entry=module_main, module_args=self.default_args)
        assert result["changed"] is False
        assert result["condition"]["name"] == self.test_condition.name

        # test update
        mocker.patch(
            self.api_class + ".run_query", side_effect=self._update_desc_side_effect
        )
        result = run_module(
            module_entry=module_main,
            module_args={**self.default_args, **{"description": "b"}},
        )
        assert result["changed"] is True
        assert self.test_condition.description == "b"

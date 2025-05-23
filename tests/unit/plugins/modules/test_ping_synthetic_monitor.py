from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ...common.utils import run_module, ModuleTestCase

from ansible_collections.newrelic.core.plugins.modules.ping_synthetic_monitor import (
    main as module_main,
)
from ansible_collections.newrelic.core.plugins.module_utils.synthetic.objects import (
    PingSyntheticMonitor,
)


class TestNrModule(ModuleTestCase):
    def __prepare(self, mocker):
        self.api_class = "ansible_collections.newrelic.core.plugins.modules.ping_synthetic_monitor.SyntheticMonitorApi"
        self.default_args = dict(
            name="foo",
            account_id="1234",
            url="foo",
            period="EVERY_MINUTE",
            public_locations=["a"],
            enabled=True,
        )
        self.test_monitor = PingSyntheticMonitor(
            name=self.default_args["name"], account_id=self.default_args["account_id"]
        )
        for k, v in self.default_args.items():
            setattr(self.test_monitor, k, v)

    def test_absent(self, mocker):
        self.__prepare(mocker)
        module_args = dict(name="foo", state="absent")

        # no difference
        mocker.patch(
            self.api_class + ".get_monitor_by_name_and_account", return_value=None
        )
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is False

        # remove monitor
        mocker.patch(
            self.api_class + ".get_monitor_by_name_and_account",
            return_value=self.test_monitor,
        )
        del_mock = mocker.patch(self.api_class + ".delete_monitor")
        result = run_module(module_entry=module_main, module_args=module_args)

        assert result["changed"] is True
        del_mock.assert_called_once()

    def _create_side_effect(self, query):
        self.test_monitor.id = 2
        self.test_monitor.guid = 1
        return {
            "data": {
                "syntheticsCreateSimpleMonitor": {
                    "monitor": {"guid": 1, "id": 2},
                    "errors": [],
                }
            }
        }

    def test_create(self, mocker):
        self.__prepare(mocker)
        mocker.patch(
            self.api_class + ".get_monitor_by_name_and_account",
            side_effect=(None, self.test_monitor),
        )
        mocker.patch(
            self.api_class + ".run_query", side_effect=self._create_side_effect
        )
        result = run_module(module_entry=module_main, module_args=self.default_args)

        assert result["changed"] is True
        assert result["monitor"]["id"] == "2"

    def _period_update_side_effect(self, **kwargs):
        self.test_monitor.period = "EVERY_5_MINUTES"
        return {
            "data": {
                "syntheticsUpdateSimpleBrowserMonitor": {
                    "monitor": {"id": 1, "guid": 2}
                }
            }
        }

    def test_update(self, mocker):
        self.__prepare(mocker)
        mocker.patch(
            self.api_class + ".get_monitor_by_name_and_account",
            return_value=self.test_monitor,
        )
        # test no change
        result = run_module(module_entry=module_main, module_args=self.default_args)
        assert result["changed"] is False
        assert result["monitor"]["name"] == self.test_monitor.name

        # test update
        mocker.patch(
            self.api_class + ".run_query",
            side_effect=self._period_update_side_effect,
        )
        result = run_module(
            module_entry=module_main,
            module_args={**self.default_args, **{"period": "EVERY_5_MINUTES"}},
        )
        assert result["changed"] is True
        assert result["monitor"]["period"] == "EVERY_5_MINUTES"

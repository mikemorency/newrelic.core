import logging
from io import StringIO
from ansible.module_utils.basic import env_fallback

from ansible_collections.newrelic.core.plugins.module_utils.nerdgraph_api_base import (
    NerdGraphQueryError,
)


logger = logging.getLogger(__name__)


class ModuleLogger:
    def __init__(self, module):
        self.logger = logging.getLogger()
        self.stdout_stream = StringIO()
        self.stderr_stream = StringIO()
        self.configure(module.params["log_level"])

    def configure(self, log_level):
        self.logger.setLevel(logging.DEBUG)
        try:
            stdout_handler = logging.StreamHandler()
            stdout_handler.setStream(self.stdout_stream)
        except AttributeError:
            # python 3.6
            stdout_handler = logging.StreamHandler(self.stdout_stream)
        stdout_handler.setLevel(log_level)

        try:
            stderr_handler = logging.StreamHandler()
            stderr_handler.setStream(self.stderr_stream)
        except AttributeError:
            # python 3.6
            stderr_handler = logging.StreamHandler(self.stderr_stream)
        stderr_handler.setLevel(logging.WARN)

        self.logger.addHandler(stdout_handler)
        self.logger.addHandler(stderr_handler)
        self.logger.addHandler(stderr_handler)

    def write_streams(self, result):
        stdout = self.stdout_stream.getvalue().strip()
        stderr = self.stderr_stream.getvalue().strip()
        if stderr:
            result["stderr"] = stderr.strip()
            result["stderr_lines"] = stderr.split("\n")

        if stdout:
            result["stdout"] = stdout
            result["stdout_lines"] = stdout.split("\n")


class ModuleBase:
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self._logger = ModuleLogger(module)

    @staticmethod
    def shared_argument_spec():
        return dict(
            api_key=dict(
                type="str",
                required=True,
                no_log=True,
                fallback=(env_fallback, ["NR_API_KEY"]),
            ),
            account_id=dict(
                type="str",
                required=True,
                fallback=(env_fallback, ["NR_ACCOUNT_ID"]),
            ),
            log_level=dict(
                type="str",
                required=False,
                fallback=(env_fallback, ["NR_LOG_LEVEL"]),
                default="WARNING",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"],
            ),
            wait_for_propegation=dict(
                type="bool",
                default=True,
            ),
            propegation_timeout=dict(
                type="int",
                default=15,
            ),
        )

    def exit_with_exception(self, result: dict, exc: Exception):
        logger.fatal("%s", exc)
        if isinstance(exc, NerdGraphQueryError):
            result["query_failure"] = exc.to_json()
        result["failed"] = True
        self._logger.write_streams(result)
        self.module.fail_json(msg=str(exc), **result)

    def exit(self, result):
        for k, v in result.items():
            if hasattr(v, "to_json"):
                result[k] = v.to_json()
        self._logger.write_streams(result)
        self.module.exit_json(**result)

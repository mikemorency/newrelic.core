from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
author:
    - Mike Morency (@mikemorency)

options:
    api_key:
      description:
          - The API key to use for authenticating with NR.
          - If this is unset, the NR_API_KEY environment variable will be used instead.
      type: str
      required: true
    account_id:
        description:
            - The ID of the account you want to use for queries against NR.
            - If this is unset, the NR_ACCOUNT_ID environment variable will be used instead.
        required: true
        type: str
    log_level:
        description:
            - The python log level to control what messages are logged
            - If this is unset, the NR_LOG_LEVEL environment variable will be used instead.
        type: str
        choices: [DEBUG, INFO, WARNING, ERROR, FATAL]
        default: WARNING
    wait_for_propegation:
        description:
            - When an object is created or changed in New Relic, the change is not visible
              from all API endpoints immediately. It can take a few seconds to fully
              propagate.
            - When true, modules will wait `propegation_timeout` seconds for the change
              to be reflected in subsequent API calls.
            - If the change is not shown after the timeout period, an error is thrown.
            - If false, modules will not confirm that the change can be seen in subsequent calls.
        default: true
        type: bool
    propegation_timeout:
        description:
            - The maximum number of seconds to wait for a change to be fully reflected in the
              New Relic API.
            - Only used if `wait_for_propegation` is true.
        default: 15
        type: int
"""

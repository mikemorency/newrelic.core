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
    entity_guids:
        description:
            - A list of entity GUIDs on which you want to manage events.
            - When creating events, an event with the same details will be created for each entity. However,
              each event will be unique and have a unique ID.
        required: true
        type: list
        elements: str
    log_level:
        description:
            - The python log level to control what messages are logged
            - If this is unset, the NR_LOG_LEVEL environment variable will be used instead.
        type: str
        choices: [DEBUG, INFO, WARNING, ERROR, FATAL]
        default: WARNING
"""

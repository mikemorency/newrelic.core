from __future__ import absolute_import, division, print_function
from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
author:
    - Mike Morency (@mikemorency)

options:
    name:
        description:
            - The exact name of the synthetic monitor to manage
        required: true
        type: str
    state:
        description:
            - Controls if the alert should be 'present' or 'absent'
        required: false
        default: present
        type: str
        choices: [present, absent]
    enabled:
        description:
            - Controls if the alert should be enabled or disabled
        required: false
        default: true
        type: bool
    period:
        description:
            - The period in which the monitor should be run. Must match the structure defined in the link below
            - https://docs.newrelic.com/docs/apis/nerdgraph/examples/nerdgraph-synthetics-tutorial/#period-attribute
        required: false
        default: EVERY_15_MINUTES
        type: str
        choices: [
            EVERY_MINUTE, EVERY_5_MINUTES, EVERY_10_MINUTES, EVERY_15_MINUTES, EVERY_30_MINUTES,
            EVERY_HOUR, EVERY_6_HOURS, EVERY_12_HOURS, EVERY_DAY
        ]
    public_locations:
        description:
            - A list of public locations that should run the synthetic check
            - https://docs.newrelic.com/docs/apis/nerdgraph/examples/nerdgraph-synthetics-tutorial/#location-field
            - Either public_locations or private_locations is required when state is present
        required: false
        default: ["AWS_US_WEST_1", "AWS_US_EAST_1", "AWS_US_EAST_2"]
        type: list
        elements: str
    private_locations:
        description:
            - A list of a private location guids that should run the synthetic check
            - Either public_locations or private_locations is required when state is present
        required: false
        default: []
        type: list
        elements: str
"""

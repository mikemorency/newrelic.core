# Ansible search paths are really obscure, especially around text files. So instead we can store these
# jinja templates as strings in a python file
class NrqlBaseClassAlertConditionTemplates:
    def __init__(self):
        pass

    @staticmethod
    def j2_delete():
        return """mutation {
            alertsConditionDelete(accountId: {{ condition.account_id }}, id: {{ condition.id }}) {
                id
            }
        }"""

    @staticmethod
    def j2_get_from_search():
        return """{
            actor {
                account(id: {{ account_id }}) {
                    alerts {
                        nrqlConditionsSearch(
                            searchCriteria: { {{ entity_search_query }} }
                            cursor: "{{ cursor }}"
                        ) {
                            totalCount
                            nextCursor
                            nrqlConditions {
                                description
                                enabled
                                entityGuid
                                id
                                name
                                nrql {
                                    query
                                }
                                runbookUrl
                                policyId
                                signal {
                                    aggregationDelay
                                    aggregationMethod
                                    aggregationTimer
                                    aggregationWindow
                                    evaluationDelay
                                    fillOption
                                    fillValue
                                    slideBy
                                }
                                terms {
                                    priority
                                    operator
                                    threshold
                                    thresholdDuration
                                    thresholdOccurrences
                                }
                                type
                            }
                        }
                    }
                }
            }
        }"""


class NrqlStaticAlertConditionTemplates:
    def __init__(self):
        pass

    @staticmethod
    def j2_create():
        return (
            "mutation {"
            "  alertsNrqlConditionStaticCreate ("
            "    accountId: {{ condition.account_id }}"
            "    policyId: {{ condition.policy_id }}"
            "    %s"
            "  ) {"
            "    id"
            "    entityGuid"
            "  }"
            "}" % NrqlStaticAlertConditionTemplates.__condition_config()
        )

    @staticmethod
    def j2_update():
        return (
            "mutation {"
            "  alertsNrqlConditionStaticUpdate ("
            "    accountId: {{ condition.account_id }},"
            "    id: {{ condition.id }},"
            "    %s"
            "  ) {"
            "    id"
            "    entityGuid"
            "  }"
            "}" % NrqlStaticAlertConditionTemplates.__condition_config()
        )

    @staticmethod
    def __condition_config():
        return (
            "condition: {"
            '  name: "{{ condition.name }}",'
            "  enabled: {{ condition.enabled | tojson }},"
            "  {% if condition.description %}"
            '  description: "{{ condition.description }}",'
            "  {% endif %}"
            "  nrql: {"
            '    query: "{{ condition.nrql_query }}"'
            "  },"
            "  {% if condition.runbook_url %}"
            '  runbookUrl: "{{ condition.runbook_url }}",'
            "  {% endif %}"
            "  signal: {"
            "    {% if condition.signal_slide_by %}"
            "    slideBy: {{ condition.signal_slide_by }},"
            "    {% endif %}"
            '    {% if condition.data_aggregation_method != "EVENT_TIMER" %}'
            "    aggregationDelay: {{ condition.data_aggregation_delay }},"
            "    {% endif %}"
            '    {% if condition.data_aggregation_method != "EVENT_FLOW" %}'
            "    aggregationTimer: {{ condition.data_aggregation_timer | tojson }},"
            "    {% endif %}"
            "    aggregationWindow: {{ condition.data_aggregation_window }},"
            "    aggregationMethod: {{ condition.data_aggregation_method }}"
            "  },"
            "  terms: ["
            "    {% for term in condition.incident_terms %}"
            "    {"
            "        threshold: {{ term.threshold }},"
            "        thresholdDuration: {{ term.duration }},"
            "        thresholdOccurrences: {{ term.occurrences }},"
            "        operator: {{ term.operator }},"
            "        priority: {{ term.priority }}"
            "    }"
            "    {% endfor %}"
            "  ],"
            "  valueFunction: SINGLE_VALUE,"
            "  violationTimeLimitSeconds: 86400"
            "}"
        )

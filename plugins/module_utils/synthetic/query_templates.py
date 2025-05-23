# Ansible search paths are really obscure, especially around text files. So instead we can store these
# jinja templates as strings in a python file
class SyntheticMonitorBaseClassTemplates:
    def __init__(self):
        pass

    @staticmethod
    def j2_delete():
        return """mutation {
            syntheticsDeleteMonitor (guid: "{{ monitor.guid }}") {
                deletedGuid
            }
        }"""

    @staticmethod
    def j2_get_from_search():
        return """{
            actor {
                entitySearch(query: "{{ entity_search_query }}") {
                    results {% if cursor %}(cursor: "{{ cursor }}") {% endif %}{
                        nextCursor
                        entities {
                            ... on SyntheticMonitorEntityOutline {
                            guid
                            name
                            accountId
                            entityType
                            monitorId
                            monitorType
                            monitoredUrl
                            period
                            monitorSummary {
                                locationsRunning
                                status
                                locationsFailing
                                successRate
                            }
                            tags {
                                key
                                values
                            }
                            type
                            }
                        }
                    }
                }
            }
        }"""


class PingSyntheticMonitorTemplates:
    def __init__(self):
        pass

    @staticmethod
    def j2_create():
        return (
            "mutation {"
            "  syntheticsCreateSimpleMonitor ("
            "    accountId: {{ monitor.account_id }},"
            "    %s"
            "  ) {"
            "    errors { description type }"
            "    monitor { guid id name }"
            "  }"
            "}" % PingSyntheticMonitorTemplates.__monitor_config()
        )

    @staticmethod
    def j2_update():
        return (
            "mutation {"
            "  syntheticsUpdateSimpleBrowserMonitor ("
            '    guid: "{{ monitor.guid }}"'
            "    %s"
            "  ) {"
            "    errors { description type }"
            "    monitor { guid id name }"
            "  }"
            "}" % PingSyntheticMonitorTemplates.__monitor_config()
        )

    @staticmethod
    def __monitor_config():
        return (
            "monitor: {"
            "  locations: {"
            "    {% if monitor.public_locations %}"
            "    public: {{ monitor.public_locations | tojson }}"
            "    {% endif %}"
            "    {% if monitor.private_locations %}"
            "    private: ["
            "      {% for location_guid in monitor.private_locations %}"
            '      {guid: "{{ location_guid }}"}'
            "      {% endfor %}"
            "    ]"
            "    {% endif %}"
            "  },"
            '  name: "{{ monitor.name }}",'
            "  period: {{ monitor.period }},"
            "  status: {{ 'ENABLED' if monitor.enabled else 'DISABLED' }},"
            '  uri: "{{ monitor.url }}",'
            "  advancedOptions: {"
            "    {% if monitor.validation_string %}"
            '    responseValidationText: "{{ monitor.validation_string }}",'
            "    {% endif %}"
            "    useTlsValidation: {{ monitor.verify_ssl | tojson }}"
            "  }"
            "}"
        )

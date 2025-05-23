# Ansible search paths are really obscure, especially around text files. So instead we can store these
# jinja templates as strings in a python file
class AlertPolicyTemplates:
    def __init__(self):
        pass

    @staticmethod
    def j2_create():
        return """mutation {
            alertsPolicyCreate(
                accountId: {{ alert_policy.account_id }}
                policy: { name: "{{ alert_policy.name }}", incidentPreference: {{ alert_policy.incident_preference }} }
            ) {
                id
                name
                incidentPreference
            }
        }"""

    @staticmethod
    def j2_update():
        return """mutation {
            alertsPolicyUpdate(
                accountId: {{ alert_policy.account_id }}
                id: {{ alert_policy.id }}
                policy: { name: "{{ alert_policy.name }}", incidentPreference: {{ alert_policy.incident_preference }} }
            ) {
                id
                name
                incidentPreference
            }
        }"""

    @staticmethod
    def j2_delete():
        return """mutation {
            alertsPolicyDelete(accountId: {{ alert_policy.account_id }}, id: {{ alert_policy.id }}) {
                id
            }
        }"""

    @staticmethod
    def j2_get_from_search():
        return """{
            actor {
                account(id: {{ account_id }}) {
                    alerts {
                        policiesSearch(searchCriteria: { {{ entity_search_query }} }) {
                            nextCursor
                            policies {
                                id
                                name
                                accountId
                                incidentPreference
                            }
                        }
                    }
                }
            }
        }"""

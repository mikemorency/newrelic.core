# Ansible search paths are really obscure, especially around text files. So instead we can store these
# jinja templates as strings in a python file
class EntityQueryTemplates:
    def __init__(self):
        pass

    @staticmethod
    def j2_get_from_search():
        return """{
            actor {
                entitySearch(query: "{{ entity_search_query }}") {
                    count
                    results {
                        entities {
                            tags {
                                key
                                values
                            }
                            accountId
                            guid
                            name
                            entityType
                            type
                        }
                    }
                }
            }
        }"""

    @staticmethod
    def j2_add_or_update_tags():
        """
        NOTE: This does not replace all of the tags. It will add tags, or update the values if the tags exist.
        """
        return """
            mutation {
                taggingAddTagsToEntity(guid: "{{ guid }}", tags: [
                    {%- for tag in tags %}
                        {key: "{{ tag.name }}", values: {{ tag.values | list | tojson }}}
                    {% endfor -%}
                ]) {
                    errors {
                        message
                        type
                    }
                }
            }
        """

    @staticmethod
    def j2_remove_tags_by_keys():
        return """
            mutation {
                taggingDeleteTagFromEntity(guid: "{{ guid }}", tagKeys: {{ tag_names | tojson }}) {
                    errors {
                        message
                        type
                    }
                }
            }
        """

    @staticmethod
    def j2_remove_tag_values():
        return """
            mutation {
                taggingDeleteTagValuesFromEntity(guid: "{{ guid }}", tagValues: [
                    {%- for tag in tags %}
                    {%- for tag_value in tag.values %}
                        {key: "{{ tag.name }}", value: "{{ tag_value }}"}
                    {% endfor -%}
                    {% endfor -%}
                ]) {
                    errors {
                        message
                        type
                    }
                }
            }
        """

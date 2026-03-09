from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
    Field,
)

from ansible_collections.newrelic.core.plugins.module_utils.models.entity import (
    EntityTags,
)


class EntityQueries:
    @staticmethod
    def entity_search(entity_search_query: str = None):
        gqlquery = GraphQLQuery(operation="query")

        tags_results_subfield = Field(name="tags", subfields=["key", "values"])
        entities_results_subfield = Field(
            name="entities",
            subfields=[
                tags_results_subfield,
                "accountId",
                "guid",
                "name",
                "entityType",
                "type",
            ],
        )
        results_field = Field(name="results", subfields=[entities_results_subfield])

        entity_search_field = Field(
            name="entitySearch",
            arguments={"query": entity_search_query},
            subfields=["count", results_field],
        )

        actor_field = Field(name="actor", subfields=[entity_search_field])

        gqlquery.fields.append(actor_field)
        return gqlquery

    @staticmethod
    def add_or_update_tags(guid: str, entity_tags: EntityTags):
        gqlquery = GraphQLQuery(operation="mutation")
        tag_list = []
        for tag in entity_tags:
            tag_list.append(dict(key=tag.name, values=tag.values))

        errors_subfield = Field(name="errors", subfields=["message", "type"])
        add_tags_field = Field(
            name="taggingAddTagsToEntity",
            arguments={"guid": guid, "tags": tag_list},
            subfields=[errors_subfield],
        )

        gqlquery.fields.append(add_tags_field)
        return gqlquery

    @staticmethod
    def remove_tags_by_keys(guid: str, tag_names: list):
        gqlquery = GraphQLQuery(operation="mutation")
        errors_subfield = Field(name="errors", subfields=["message", "type"])
        delete_tags_field = Field(
            name="taggingDeleteTagFromEntity",
            arguments={"guid": guid, "tagKeys": tag_names},
            subfields=[errors_subfield],
        )

        gqlquery.fields.append(delete_tags_field)
        return gqlquery

    @staticmethod
    def remove_tag_values(guid: str, entity_tags: EntityTags):
        gqlquery = GraphQLQuery(operation="mutation")
        tag_values_list = []
        for tag in entity_tags:
            for tag_value in tag.values:
                tag_values_list.append(dict(key=tag.name, value=tag_value))

        errors_subfield = Field(name="errors", subfields=["message", "type"])
        delete_tags_field = Field(
            name="taggingDeleteTagValuesFromEntity",
            arguments={"guid": guid, "tagValues": tag_values_list},
            subfields=[errors_subfield],
        )

        gqlquery.fields.append(delete_tags_field)
        return gqlquery

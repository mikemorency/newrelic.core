from ansible_collections.newrelic.core.plugins.module_utils.graphql.query import (
    GraphQLQuery,
    Field,
    add_to_dict_if_not_none
)


class ChangeTrackingDeploymentQueries():
    @staticmethod
    def entity_search(guid: str, entity_search_query: str = None, start_time: int = None, end_time: int = None):
        filter = dict(limit=2000, timeWindow=dict())
        add_to_dict_if_not_none(filter['timeWindow'], 'startTime', start_time)
        add_to_dict_if_not_none(filter['timeWindow'], 'endTime', end_time)
        add_to_dict_if_not_none(filter, 'query', entity_search_query)

        gqlquery = GraphQLQuery()

        results_field = Field(
            name="results",
            subfields=[
                "changelog",
                "commit",
                "deepLink",
                "deploymentId",
                "deploymentType",
                "description",
                "entityGuid",
                "groupId",
                "timestamp",
                "user",
                "version"
            ]
        )

        deployment_search_field = Field(
            name="deploymentSearch",
            arguments=filter,
            subfields=[
                results_field
            ]
        )

        entity_field = Field(
            name="entity",
            arguments={"guid": guid},
            subfields=[
                deployment_search_field
            ]
        )

        actor_field = Field (
            name="actor",
            subfields=[
                entity_field
            ]
        )

        gqlquery.fields.append(actor_field)
        return gqlquery

    @staticmethod
    def create(deployment_event, append_to_query: GraphQLQuery = None):
        if not append_to_query:
            gqlquery = GraphQLQuery()
        else:
            gqlquery = append_to_query

        event_dict = dict(
            entityGuid=deployment_event.entity_guid,
            version=deployment_event.version
        )
        add_to_dict_if_not_none(event_dict, 'changelog', deployment_event.changelog)
        add_to_dict_if_not_none(event_dict, 'commit', deployment_event.commit)
        add_to_dict_if_not_none(event_dict, 'deepLink', deployment_event.deep_link)
        add_to_dict_if_not_none(event_dict, 'deploymentType', deployment_event.deployment_type)
        add_to_dict_if_not_none(event_dict, 'description', deployment_event.description)
        add_to_dict_if_not_none(event_dict, 'groupId', deployment_event.group_id)
        add_to_dict_if_not_none(event_dict, 'timestamp', deployment_event.timestamp)
        add_to_dict_if_not_none(event_dict, 'user', deployment_event.user)

        create_field = Field(
            name="changeTrackingCreateDeployment",
            arguments={"deployment": event_dict},
            subfields=[
                "deploymentId",
                "entityGuid"
            ]
        )

        mutation_field = Field (
            name="mutation",
            subfields=[
                create_field
            ]
        )

        gqlquery.fields.append(mutation_field)
        return gqlquery

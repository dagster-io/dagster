import {graphql} from '../graphql';

export const SCHEDULES_ROOT_QUERY = graphql(`
  query SchedulesRootQuery(
    $repositorySelector: RepositorySelector!
    $instigationType: InstigationType!
  ) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        ...RepositorySchedulesFragment
      }
      ...PythonErrorFragment
    }
    unloadableInstigationStatesOrError(instigationType: $instigationType) {
      ... on InstigationStates {
        results {
          id
          ...InstigationStateFragment
        }
      }
      ...PythonErrorFragment
    }
    instance {
      ...InstanceHealthFragment
    }
  }

  fragment RepositorySchedulesFragment on Repository {
    name
    id
    location {
      id
      name
    }
    schedules {
      id
      ...ScheduleFragment
    }
    ...RepositoryInfoFragment
  }

  fragment ScheduleFragment on Schedule {
    id
    name
    cronSchedule
    executionTimezone
    pipelineName
    solidSelection
    mode
    description
    partitionSet {
      id
      name
    }
    scheduleState {
      id
      ...InstigationStateFragment
    }
    futureTicks(limit: 5) {
      results {
        timestamp
      }
    }
  }
`);

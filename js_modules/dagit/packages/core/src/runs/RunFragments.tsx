import {graphql} from '../graphql';

export const RUN_FRAGMENT_FOR_REPOSITORY_MATCH = graphql(`
  fragment RunFragmentForRepositoryMatch on Run {
    id
    pipelineName
    pipelineSnapshotId
    parentPipelineSnapshotId
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
  }
`);

export const RunFragments = graphql(`
  fragment RunFragment on Run {
    id
    runConfigYaml
    runId
    canTerminate
    status
    mode
    tags {
      key
      value
    }
    assets {
      id
      key {
        path
      }
    }
    rootRunId
    parentRunId
    pipelineName
    solidSelection
    assetSelection {
      ... on AssetKey {
        path
      }
    }
    pipelineSnapshotId
    parentPipelineSnapshotId
    executionPlan {
      artifactsPersisted
      ...ExecutionPlanToGraphFragment
    }
    stepKeysToExecute
    ...RunFragmentForRepositoryMatch
    ...RunDetailsFragment
    updateTime
    stepStats {
      stepKey
      status
      startTime
      endTime
      attempts {
        startTime
        endTime
      }
      markers {
        startTime
        endTime
      }
    }
  }

  fragment RunDagsterRunEventFragment on DagsterRunEvent {
    ... on MessageEvent {
      message
      timestamp
      level
      stepKey
    }

    ...LogsScrollingTableMessageFragment
    ...RunMetadataProviderMessageFragment
  }
`);

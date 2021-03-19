import {RunFragmentForRepositoryMatch} from '../runs/types/RunFragmentForRepositoryMatch';

import {DagsterRepoOption, useRepositoryOptions} from './WorkspaceContext';
import {findRepoContainingPipeline, repoContainsPipeline} from './findRepoContainingPipeline';

type MatchType = {
  match: DagsterRepoOption;
  type: 'origin' | 'snapshot' | 'pipeline-name';
};

/**
 * Given a Run fragment, find the repository that contains its pipeline.
 */
export const useRepositoryForRun = (
  run: RunFragmentForRepositoryMatch | null | undefined,
): MatchType | null => {
  const {options} = useRepositoryOptions();

  if (!run) {
    return null;
  }

  const pipelineName = run.pipeline.name;
  const snapshotId = run.pipelineSnapshotId;

  // Find the repository that contains the specified pipeline name and snapshot ID, if any.
  // This is our surest repo match for this run.
  if (pipelineName && snapshotId) {
    const snapshotMatches = findRepoContainingPipeline(options, pipelineName, snapshotId);
    if (snapshotMatches.length) {
      return {match: snapshotMatches[0], type: 'snapshot'};
    }
  }

  // Otherwise, try to match the pipeline name within the specified origin, if any.
  const origin = run.repositoryOrigin;

  if (origin) {
    const location = origin?.repositoryLocationName;
    const name = origin?.repositoryName;

    const match = options.find(
      (option) => option.repository.name === name && option.repositoryLocation.name === location,
    );

    // The origin repo is loaded. Verify that a pipeline with this name exists and return the match if so.
    if (match && repoContainsPipeline(match, pipelineName)) {
      return {match, type: 'pipeline-name'};
    }

    // Could not find this pipeline within the origin repo.
    return null;
  }

  // There is no origin repo. Fall back to the first pipeline name match.
  const possibleMatches = findRepoContainingPipeline(options, pipelineName);
  if (possibleMatches.length) {
    return {match: possibleMatches[0], type: 'pipeline-name'};
  }

  return null;
};

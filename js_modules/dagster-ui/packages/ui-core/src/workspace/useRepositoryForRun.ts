import {DagsterRepoOption, useRepositoryOptions} from './WorkspaceContext/util';
import {findRepoContainingPipeline, repoContainsPipeline} from './findRepoContainingPipeline';

type MatchType = {
  match: DagsterRepoOption;
  type: 'origin' | 'pipeline-name-only';
};

type MatchTypeWithSnapshot = {
  match: DagsterRepoOption;
  type: 'origin-and-snapshot' | 'origin-only' | 'snapshot-only' | 'pipeline-name-only';
};

export interface TargetRunWithParentSnapshot extends TargetRun {
  parentPipelineSnapshotId?: string | null;
}

interface TargetRun {
  pipelineName: string;
  repositoryOrigin: null | {
    repositoryLocationName: string;
    repositoryName: string;
  };
  pipelineSnapshotId: string | null;
}

const repoOriginMatchForRun = (options: DagsterRepoOption[], run: TargetRun | null | undefined) => {
  if (!run) {
    return null;
  }

  const pipelineName = run.pipelineName;
  // Try to match the pipeline name within the specified origin, if possible.
  const origin = run.repositoryOrigin;

  if (!origin) {
    return null;
  }

  const location = origin?.repositoryLocationName;
  const name = origin?.repositoryName;

  const match = options.find(
    (option) => option.repository.name === name && option.repositoryLocation.name === location,
  );

  // The origin repo is loaded. Verify that a pipeline with this name exists and return the match if so.
  return match && repoContainsPipeline(match, pipelineName) ? match : null;
};

const jobNameMatchesForRun = (
  options: DagsterRepoOption[],
  run: TargetRun | null | undefined,
): DagsterRepoOption[] | null => {
  if (!run) {
    return null;
  }

  const pipelineName = run.pipelineName;

  // There is no origin repo. Find any repos that might contain a matching pipeline name.
  const possibleMatches = findRepoContainingPipeline(options, pipelineName);
  return possibleMatches.length ? possibleMatches : null;
};

const snapshotMatchesForRun = (
  options: DagsterRepoOption[],
  run: TargetRunWithParentSnapshot | null | undefined,
): DagsterRepoOption[] | null => {
  if (!run) {
    return null;
  }

  const pipelineName = run.pipelineName;

  // When jobs are subsetted (with an opSelection or assetSelection), only their
  // parentPipelineSnapshotId (the id of the pipelineSnapshot that they were subsetted from) will
  // be found in the repository, so look for that instead.
  const snapshotId = run.parentPipelineSnapshotId ?? run.pipelineSnapshotId;

  // Find the repository that contains the specified pipeline name and snapshot ID, if any.
  if (pipelineName && snapshotId) {
    const snapshotMatches = findRepoContainingPipeline(options, pipelineName, snapshotId);
    if (snapshotMatches.length) {
      return snapshotMatches;
    }
  }

  return null;
};

/**
 * The simple case. Find the repo match for this job name, or the first available
 * repo match for that job name.
 */
export const useRepositoryForRunWithoutSnapshot = (
  run: TargetRun | null | undefined,
): MatchType | null => {
  const {options} = useRepositoryOptions();
  const repoMatch = repoOriginMatchForRun(options, run);
  if (repoMatch) {
    return {match: repoMatch, type: 'origin'};
  }
  const jobNameMatches = jobNameMatchesForRun(options, run);
  if (jobNameMatches && jobNameMatches.length) {
    return {match: jobNameMatches[0]!, type: 'pipeline-name-only'};
  }
  return null;
};

/**
 * The more complex case, where a parent snapshot has been fetched. Here, use a
 * repo match and try to pair it with the snapshot ID. If that fails, use any repo
 * match, then any snapshot ID match, then any job name match.
 *
 * Retrieving a parent snapshot ID is expensive, so this should only be used for
 * one run at a time.
 */
export const useRepositoryForRunWithParentSnapshot = (
  run: TargetRunWithParentSnapshot | null | undefined,
): MatchTypeWithSnapshot | null => {
  const {options} = useRepositoryOptions();

  const repoMatch = repoOriginMatchForRun(options, run);
  const snapshotMatches = snapshotMatchesForRun(options, run);
  const jobNameMatches = jobNameMatchesForRun(options, run);

  if (repoMatch) {
    if (snapshotMatches) {
      const repoAndSnapshotMatch = snapshotMatches.find(
        (repoOption) =>
          repoOption.repository.name === repoMatch.repository.name &&
          repoOption.repositoryLocation.name === repoMatch.repositoryLocation.name,
      );
      if (repoAndSnapshotMatch) {
        return {match: repoAndSnapshotMatch, type: 'origin-and-snapshot'};
      }
    }

    return {match: repoMatch, type: 'origin-only'};
  }

  if (snapshotMatches && snapshotMatches[0]) {
    return {match: snapshotMatches[0], type: 'snapshot-only'};
  }

  if (jobNameMatches && jobNameMatches[0]) {
    return {match: jobNameMatches[0], type: 'pipeline-name-only'};
  }

  return null;
};

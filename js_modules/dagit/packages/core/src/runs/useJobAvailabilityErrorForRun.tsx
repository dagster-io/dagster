import {Group, IconName} from '@dagster-io/ui';
import * as React from 'react';

import {buildRepoAddress, buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {
  TargetRunWithParentSnapshot,
  useRepositoryForRunWithParentSnapshot,
} from '../workspace/useRepositoryForRun';

export const useJobAvailabilityErrorForRun = (
  run: TargetRunWithParentSnapshot | null | undefined,
): null | {tooltip?: string | JSX.Element; icon?: IconName; disabled: boolean} => {
  const repoMatch = useRepositoryForRunWithParentSnapshot(run);

  // The run hasn't loaded, so no error.
  if (!run) {
    return null;
  }

  if (!run.pipelineSnapshotId) {
    return {
      icon: 'error',
      tooltip: `"${run.pipelineName}" could not be found.`,
      disabled: true,
    };
  }

  if (repoMatch) {
    const {type: matchType} = repoMatch;

    // The run matches the repository and active snapshot ID for the job. This is the best
    // we can do, so consider it safe to run as-is.
    if (matchType === 'origin-and-snapshot') {
      return null;
    }

    // Beyond this point, we're just trying our best. Warn the user that behavior might not be what
    // they expect.

    if (matchType === 'origin-only') {
      // Only the repo is a match.
      return {
        icon: 'warning',
        tooltip: `The loaded version of "${run.pipelineName}" may be different than the one used for the original run.`,
        disabled: false,
      };
    }

    if (matchType === 'snapshot-only') {
      // Only the snapshot ID matched, but not the repo.
      const originRepoName = run.repositoryOrigin
        ? repoAddressAsHumanString(
            buildRepoAddress(
              run.repositoryOrigin.repositoryName,
              run.repositoryOrigin.repositoryLocationName,
            ),
          )
        : null;

      return {
        icon: 'warning',
        tooltip: (
          <Group direction="column" spacing={4}>
            <div>{`The original run loaded "${run.pipelineName}" from ${
              originRepoName || 'a different code location'
            }.`}</div>
            {originRepoName ? (
              <div>
                Original definition in: <strong>{originRepoName}</strong>
              </div>
            ) : null}
          </Group>
        ),
        disabled: false,
      };
    }

    // Only the job name matched. This could be from any repo in the workspace.
    return {
      icon: 'warning',
      tooltip: `The job "${run.pipelineName}" may be a different version from the original pipeline run.`,
      disabled: false,
    };
  }

  // We could not find a repo that contained this job. Inform the user that they should
  // load the missing repository.
  const repoForRun = run.repositoryOrigin?.repositoryName;
  const repoLocationForRun = run.repositoryOrigin?.repositoryLocationName;

  const tooltip = (
    <Group direction="column" spacing={8}>
      <div>{`"${run.pipelineName}" is not available in your definitions.`}</div>
      {repoForRun && repoLocationForRun ? (
        <div>{`Load definitions for ${buildRepoPathForHuman(
          repoForRun,
          repoLocationForRun,
        )} and try again.`}</div>
      ) : null}
    </Group>
  );

  return {
    icon: 'error',
    tooltip,
    disabled: true,
  };
};

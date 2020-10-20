import Fuse from 'fuse.js';
import * as React from 'react';

import {sampleData} from 'src/search/sample/data';
import {SearchResult, SearchResultType} from 'src/search/types';
import {workspacePath} from 'src/workspace/workspacePath';

const fuseOptions = {
  keys: ['label', 'tags', 'type'],
  threshold: 0.3,
};

const repositoryDataToSearchResults = (data: typeof sampleData) => {
  const {repositoriesOrError} = data;
  if (repositoriesOrError.__typename !== 'RepositoryConnection') {
    return new Fuse([]);
  }

  const {nodes} = repositoriesOrError;
  const assetKeys = new Set<string>();
  const manyRepos = nodes.length > 1;

  const allEntries = nodes.reduce((accum, repo) => {
    const {name, location, pipelines} = repo;
    const {name: locationName} = location;
    const repoAddress = `${name}@${locationName}`;

    const repoResult = {
      key: repoAddress,
      label: repoAddress,
      description: `Repository`,
      href: workspacePath(name, locationName),
      type: SearchResultType.Repository,
    };

    const resultsPerPipeline = pipelines.map((pipeline) => {
      const pipelineResult = {
        key: `${repoAddress}-${pipeline.name}`,
        label: pipeline.name,
        description: manyRepos ? `Pipeline in ${repoAddress}` : 'Pipeline',
        href: workspacePath(name, locationName, `/pipelines/${pipeline.name}`),
        type: SearchResultType.Pipeline,
      };

      const allSchedules = pipeline.schedules.map((schedule) => ({
        key: `${repoAddress}-${schedule.name}`,
        label: schedule.name,
        description: manyRepos ? `Schedule in ${repoAddress}` : 'Schedule',
        href: workspacePath(name, locationName, `/schedules/${schedule.name}`),
        type: SearchResultType.Schedule,
      }));

      const allRuns = pipeline.runs.map((run) => {
        const {assets} = run;
        assets.forEach((asset) => {
          const assetKey = asset.key.path.join('.');
          assetKeys.add(assetKey);
        });

        return {
          key: `${repoAddress}-${run.runId}`,
          label: run.runId,
          description: `Run of ${pipeline.name}`,
          href: `/instance/runs/${run.runId}`,
          type: SearchResultType.Run,
          tags: run.tags.map((tag) => `${tag.key}:${tag.value}`).join(' '),
        };
      });

      return [...accum, pipelineResult, ...allRuns, ...allSchedules];
    });

    const allSolids = repo.usedSolids.map((solid) => ({
      key: `${repoAddress}-${solid.definition.name}`,
      label: solid.definition.name,
      description: manyRepos ? `Solid in ${repoAddress}` : 'Solid',
      href: workspacePath(name, locationName, `/solids/${solid.definition.name}`),
      type: SearchResultType.Solid,
    }));

    const allAssets = Array.from(assetKeys).map((assetKey) => ({
      key: assetKey,
      label: assetKey,
      description: `Asset`,
      href: `/instance/assets/${assetKey.replace('.', '/')}`,
      type: SearchResultType.Asset,
    }));

    return [
      repoResult,
      ...allSolids,
      ...allAssets,
      ...resultsPerPipeline.reduce((accum, results) => [...accum, ...results], []),
    ];
  }, []);

  return new Fuse(allEntries, fuseOptions);
};

export const useRepoSearch = () => {
  const fuse = React.useMemo(() => repositoryDataToSearchResults(sampleData), []);
  return React.useCallback(
    (queryString: string): Fuse.FuseResult<SearchResult>[] => fuse.search(queryString),
    [fuse],
  );
};

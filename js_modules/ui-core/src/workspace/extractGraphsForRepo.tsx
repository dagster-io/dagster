import {RepositoryGraphsFragment} from './types/WorkspaceGraphsQuery.types';
import {COMMON_COLLATOR} from '../app/Util';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

type Graph = {name: string; path: string; description: string | null};

export const extractGraphsForRepo = (repo: RepositoryGraphsFragment) => {
  const jobGraphNames = new Set<string>(
    repo.pipelines.filter((p) => p.isJob && !isHiddenAssetGroupJob(p.name)).map((p) => p.graphName),
  );

  const items: Graph[] = Array.from(jobGraphNames).map((graphName) => ({
    name: graphName,
    path: `/graphs/${graphName}`,
    description: null,
  }));

  repo.usedSolids.forEach((s) => {
    if (s.definition.__typename === 'CompositeSolidDefinition') {
      const invocation = s.invocations[0];
      if (invocation) {
        items.push({
          name: s.definition.name,
          path: `/graphs/${invocation.pipeline.name}/${invocation.solidHandle.handleID}/`,
          description: s.definition.description,
        });
      }
    }
  });

  return items.sort((a, b) => COMMON_COLLATOR.compare(a.name, b.name));
};

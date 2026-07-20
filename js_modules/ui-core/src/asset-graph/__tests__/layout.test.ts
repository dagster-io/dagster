import {FeatureFlag} from '@shared/FeatureFlags';

import {getCurrentFeatureFlags, setFeatureFlags} from '../../app/Flags';
import {
  buildAssetKey,
  buildAssetNode,
  buildRepository,
  buildRepositoryLocation,
} from '../../graphql/builders';
import {layoutAssetGraphImpl} from '../layout';
import {GraphData, GraphNode, groupIdForNode, toGraphId} from '../Utils';

describe('layoutAssetGraphImpl', () => {
  const featureFlags = getCurrentFeatureFlags();

  beforeEach(() => {
    setFeatureFlags({...featureFlags, [FeatureFlag.flagAssetGraphGroupsPerCodeLocation]: false});
  });

  afterEach(() => {
    setFeatureFlags(featureFlags);
  });

  const graphNode = (name: string, groupName: string): GraphNode => {
    const assetKey = buildAssetKey({path: [name]});
    return {
      id: toGraphId(assetKey),
      assetKey,
      definition: buildAssetNode({
        assetKey,
        groupName,
        repository: buildRepository({
          name: 'repository',
          location: buildRepositoryLocation({name: 'location'}),
        }),
      }),
    };
  };

  it('routes lineage from an expanded group into a collapsed downstream group', () => {
    const first = graphNode('first', 'source');
    const second = graphNode('second', 'source');
    const third = graphNode('third', 'source');
    const target = graphNode('target', 'downstream');
    const graphData: GraphData = {
      nodes: {
        [first.id]: first,
        [second.id]: second,
        [third.id]: third,
        [target.id]: target,
      },
      downstream: {
        [first.id]: {[second.id]: true},
        [second.id]: {[third.id]: true},
        [third.id]: {[target.id]: true},
        [target.id]: {},
      },
      upstream: {
        [first.id]: {},
        [second.id]: {[first.id]: true},
        [third.id]: {[second.id]: true},
        [target.id]: {[third.id]: true},
      },
      expandedGroups: [groupIdForNode(first)],
    };

    const layout = layoutAssetGraphImpl(graphData, {
      direction: 'horizontal',
      facets: [],
      flagAssetGraphGroupsPerCodeLocation: false,
    });
    const edge = layout.edges.find(({toId}) => toId === groupIdForNode(target));
    const thirdLayout = layout.nodes[third.id];

    expect(edge).toBeDefined();
    expect(edge?.fromId).toBe(third.id);
    expect(edge?.sourceBoundary).toBeDefined();
    expect(edge?.targetBoundary).toBeDefined();
    expect(edge!.targetBoundary! - edge!.sourceBoundary!).toBeGreaterThanOrEqual(60);
    expect(edge?.from.y).toBe(thirdLayout!.bounds.y + thirdLayout!.bounds.height / 2);
  });
});

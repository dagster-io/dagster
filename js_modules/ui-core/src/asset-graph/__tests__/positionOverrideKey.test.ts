import {AssetGraphViewType} from '../Utils';

describe('getPositionOverrideKey', () => {
  it('scopes asset group overrides by group identity instead of the fallback explorer pipeline name', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const {getPositionOverrideKey} = require('../positionOverrideKey');

    const keyA = getPositionOverrideKey({
      viewType: AssetGraphViewType.GROUP,
      explorerPath: {pipelineName: 'lineage', opsQuery: '', opNames: []},
      fetchOptions: {
        groupSelector: {
          groupName: 'analytics',
          repositoryName: 'repo_a',
          repositoryLocationName: 'location_a',
        },
      },
    });
    const keyB = getPositionOverrideKey({
      viewType: AssetGraphViewType.GROUP,
      explorerPath: {pipelineName: 'lineage', opsQuery: '', opNames: []},
      fetchOptions: {
        groupSelector: {
          groupName: 'finance',
          repositoryName: 'repo_b',
          repositoryLocationName: 'location_b',
        },
      },
    });

    expect(keyA).not.toEqual(keyB);
  });

  it('includes the graph query in the persisted scope for global views', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const {getPositionOverrideKey} = require('../positionOverrideKey');

    expect(
      getPositionOverrideKey({
        viewType: AssetGraphViewType.GLOBAL,
        explorerPath: {pipelineName: '', opsQuery: 'group:"analytics"', opNames: []},
        fetchOptions: {},
      }),
    ).not.toEqual(
      getPositionOverrideKey({
        viewType: AssetGraphViewType.GLOBAL,
        explorerPath: {pipelineName: '', opsQuery: 'group:"finance"', opNames: []},
        fetchOptions: {},
      }),
    );
  });

  it('distinguishes job graphs with the same pipeline name in different repos', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const {getPositionOverrideKey} = require('../positionOverrideKey');

    expect(
      getPositionOverrideKey({
        viewType: AssetGraphViewType.JOB,
        explorerPath: {pipelineName: 'daily_assets', opsQuery: '', opNames: []},
        fetchOptions: {
          pipelineSelector: {
            pipelineName: 'daily_assets',
            repositoryName: 'repo_a',
            repositoryLocationName: 'location_a',
          },
        },
      }),
    ).not.toEqual(
      getPositionOverrideKey({
        viewType: AssetGraphViewType.JOB,
        explorerPath: {pipelineName: 'daily_assets', opsQuery: '', opNames: []},
        fetchOptions: {
          pipelineSelector: {
            pipelineName: 'daily_assets',
            repositoryName: 'repo_b',
            repositoryLocationName: 'location_b',
          },
        },
      }),
    );
  });
});

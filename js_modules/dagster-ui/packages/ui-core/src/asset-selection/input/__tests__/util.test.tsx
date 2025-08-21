import {observeEnabled} from 'shared/app/observeEnabled.oss';

import {AssetGraphQueryItem} from '../../../asset-graph/types';
import {AssetHealthStatus} from '../../../graphql/types';
import {SUB_STATUSES, getAttributesMap} from '../util';

// Mock the observeEnabled function
jest.mock('shared/app/observeEnabled.oss', () => ({
  observeEnabled: jest.fn(),
}));

const mockObserveEnabled = observeEnabled as jest.MockedFunction<typeof observeEnabled>;

describe('getAttributesMap', () => {
  const mockAssets: AssetGraphQueryItem[] = [
    {
      name: 'asset1',
      inputs: [],
      outputs: [],
      node: {
        assetKey: {path: ['asset1']},
        tags: [],
        owners: [],
        groupName: null,
        kinds: [],
        repository: {
          name: 'repo1',
          location: {name: 'location1'},
        },
      },
    } as unknown as AssetGraphQueryItem,
    {
      name: 'asset2',
      inputs: [],
      outputs: [],
      node: {
        assetKey: {path: ['asset2']},
        tags: [],
        owners: [],
        groupName: null,
        kinds: [],
        repository: {
          name: 'repo2',
          location: {name: 'location2'},
        },
      },
    } as unknown as AssetGraphQueryItem,
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not include status attribute when observeEnabled is false', () => {
    mockObserveEnabled.mockReturnValue(false);

    const result = getAttributesMap(mockAssets);

    expect(result).not.toHaveProperty('status');
    expect(result).toEqual({
      key: ['asset1', 'asset2'],
      tag: [],
      owner: [''],
      group: [''],
      kind: [''],
      code_location: ['repo1@location1', 'repo2@location2'],
    });
  });

  it('should include status attribute when observeEnabled is true', () => {
    mockObserveEnabled.mockReturnValue(true);

    const result = getAttributesMap(mockAssets);

    expect((result as any).status).toEqual(expect.arrayContaining(SUB_STATUSES));
  });

  it('should handle empty assets array', () => {
    mockObserveEnabled.mockReturnValue(true);

    const result = getAttributesMap([]);

    expect(result).toEqual({
      key: [],
      tag: [],
      owner: [],
      group: [],
      kind: [],
      code_location: [],
      status: [
        AssetHealthStatus.HEALTHY,
        AssetHealthStatus.DEGRADED,
        AssetHealthStatus.WARNING,
        AssetHealthStatus.UNKNOWN,
        AssetHealthStatus.NOT_APPLICABLE,
        ...SUB_STATUSES,
      ],
    });
  });
});

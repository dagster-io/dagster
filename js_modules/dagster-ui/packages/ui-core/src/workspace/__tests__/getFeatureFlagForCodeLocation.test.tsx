import {buildFeatureFlag, buildWorkspaceLocationEntry} from '../../graphql/types';
import {WorkspaceLocationNodeFragment} from '../WorkspaceContext/types/WorkspaceQueries.types';
import {getFeatureFlagForCodeLocation} from '../WorkspaceContext/util';

describe('getFeatureFlagForCodeLocation', () => {
  const locationEntries: WorkspaceLocationNodeFragment[] = [
    buildWorkspaceLocationEntry({
      id: 'foo',
      featureFlags: [
        buildFeatureFlag({
          name: 'LOREM',
          enabled: false,
        }),
        buildFeatureFlag({
          name: 'IPSUM',
          enabled: true,
        }),
      ],
    }),
  ];

  it('returns true for an enabled flag in a matching code location', () => {
    expect(getFeatureFlagForCodeLocation(locationEntries, 'foo', 'IPSUM')).toBe(true);
  });

  it('returns false for a disabled flag in a matching code location', () => {
    expect(getFeatureFlagForCodeLocation(locationEntries, 'foo', 'LOREM')).toBe(false);
  });

  it('returns false for a flag that cannot be found in a matching code location', () => {
    expect(getFeatureFlagForCodeLocation(locationEntries, 'foo', 'FAKE_FLAG')).toBe(false);
  });

  it('returns false for an existing flag that cannot be found in an unknown code location', () => {
    expect(getFeatureFlagForCodeLocation(locationEntries, 'FAKE_LOCATION', 'IPSUM')).toBe(false);
  });

  it('returns false for an unknown flag in an unknown code location', () => {
    expect(getFeatureFlagForCodeLocation(locationEntries, 'FAKE_LOCATION', 'FAKE_FLAG')).toBe(
      false,
    );
  });
});

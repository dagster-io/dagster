import {MockedProvider} from '@apollo/client/testing';
import {renderHook} from '@testing-library/react-hooks';

import {buildFeatureFlag, buildPythonError, buildWorkspaceLocationEntry} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {
  LocationFeatureFlagsQuery,
  LocationFeatureFlagsQueryVariables,
} from '../types/WorkspaceLocationFeatureFlags.types';
import {
  LOCATION_FEATURE_FLAGS_QUERY,
  useFeatureFlagForCodeLocation,
} from '../useFeatureFlagForCodeLocation';

describe('WorkspaceLocationFeatureFlags', () => {
  const mock1 = buildQueryMock<LocationFeatureFlagsQuery, LocationFeatureFlagsQueryVariables>({
    query: LOCATION_FEATURE_FLAGS_QUERY,
    variables: {
      name: 'foo',
    },
    data: {
      workspaceLocationEntryOrError: buildWorkspaceLocationEntry({
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
    },
  });

  const mock2 = buildQueryMock<LocationFeatureFlagsQuery, LocationFeatureFlagsQueryVariables>({
    query: LOCATION_FEATURE_FLAGS_QUERY,
    variables: {
      name: 'FAKE_LOCATION',
    },
    data: {
      workspaceLocationEntryOrError: buildPythonError(),
    },
  });

  function render(locationName: string, flagName: string) {
    return renderHook(() => useFeatureFlagForCodeLocation(locationName, flagName), {
      wrapper: ({children}: {children: React.ReactNode}) => (
        <MockedProvider mocks={[mock1, mock2]}>{children}</MockedProvider>
      ),
    });
  }

  it('returns true for an enabled flag in a matching code location', async () => {
    const hookResult = render('foo', 'IPSUM');
    // Initially false while loading
    expect(hookResult.result.current).toBe(false);
    await hookResult.waitForValueToChange(() => hookResult.result.current);
    expect(hookResult.result.current).toBe(true);
  });

  it('returns false for a disabled flag in a matching code location', async () => {
    const hookResult = render('foo', 'LOREM');
    expect(hookResult.result.current).toBe(false);
    await hookResult.waitForNextUpdate();
    expect(hookResult.result.current).toBe(false);
  });

  it('returns false for a flag that cannot be found in a matching code location', async () => {
    const hookResult = render('foo', 'FAKE_FLAG');
    expect(hookResult.result.current).toBe(false);
    await hookResult.waitForNextUpdate();
    expect(hookResult.result.current).toBe(false);
  });

  it('returns false for an existing flag that cannot be found in an unknown code location', async () => {
    const hookResult = render('FAKE_LOCATION', 'IPSUM');
    expect(hookResult.result.current).toBe(false);
    await hookResult.waitForNextUpdate();
    expect(hookResult.result.current).toBe(false);
  });

  it('returns false for an unknown flag in an unknown code location', async () => {
    const hookResult = render('FAKE_LOCATION', 'FAKE_FLAG');
    expect(hookResult.result.current).toBe(false);
    await hookResult.waitForNextUpdate();
    expect(hookResult.result.current).toBe(false);
  });
});

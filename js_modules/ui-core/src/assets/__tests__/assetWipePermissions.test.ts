import {PermissionResult} from '../../app/Permissions';
import {assetHasWipePermission} from '../assetWipePermissions';

const wipePermissions = (enabled: boolean): {canWipeAssets: PermissionResult} => ({
  canWipeAssets: {enabled, disabledReason: enabled ? '' : 'Not allowed'},
});

describe('assetHasWipePermission', () => {
  it.each([
    {
      name: 'deployment-wide permission',
      unscoped: true,
      location: false,
      definition: false,
      expected: true,
    },
    {
      name: 'code location permission',
      unscoped: false,
      location: true,
      definition: false,
      expected: true,
    },
    {
      name: 'per-asset permission',
      unscoped: false,
      location: false,
      definition: true,
      expected: true,
    },
    {
      name: 'no permission',
      unscoped: false,
      location: false,
      definition: false,
      expected: false,
    },
  ])('returns $expected with $name', ({unscoped, location, definition, expected}) => {
    expect(
      assetHasWipePermission(
        {
          definitionHasWipePermission: definition,
          locationName: 'location-a',
        },
        wipePermissions(unscoped),
        {'location-a': wipePermissions(location)},
      ),
    ).toBe(expected);
  });

  it('does not use permission from a different code location', () => {
    expect(
      assetHasWipePermission(
        {
          definitionHasWipePermission: false,
          locationName: 'location-a',
        },
        wipePermissions(false),
        {'location-b': wipePermissions(true)},
      ),
    ).toBe(false);
  });
});

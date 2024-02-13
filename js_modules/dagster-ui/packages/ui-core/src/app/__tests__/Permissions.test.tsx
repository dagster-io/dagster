import permissions from '../../graphql/permissions.json';
import {EXPECTED_PERMISSIONS, extractPermissions} from '../Permissions';
import {PermissionFragment} from '../types/Permissions.types';

describe('Permissions', () => {
  it('Client permissions match graphql permissions', () => {
    permissions.forEach(({permission}: {permission: any}) => {
      expect(permission in EXPECTED_PERMISSIONS).toBe(true);
    });
  });

  describe('Fallback permissions', () => {
    const permissions: PermissionFragment[] = [
      {
        __typename: 'Permission',
        permission: 'launch_pipeline_execution',
        value: false,
        disabledReason: 'u cannot',
      },
      {
        __typename: 'Permission',
        permission: 'edit_sensor',
        value: true,
        disabledReason: null,
      },
    ];

    const fallback: PermissionFragment[] = [
      {
        __typename: 'Permission',
        permission: 'launch_pipeline_execution',
        value: false,
        disabledReason: 'u cannot',
      },
      {
        __typename: 'Permission',
        permission: 'edit_sensor',
        value: false,
        disabledReason: 'no dice',
      },
      {
        __typename: 'Permission',
        permission: 'start_schedule',
        value: true,
        disabledReason: null,
      },
    ];

    it('extracts permissions with no fallback', () => {
      const extracted = extractPermissions(permissions);
      expect(extracted.canLaunchPipelineExecution).toEqual({
        enabled: false,
        disabledReason: 'u cannot',
      });
      expect(extracted.canStopSensor).toEqual({
        enabled: true,
        disabledReason: '',
      });

      // Falls back to base default permission
      expect(extracted.canStartSchedule).toEqual({
        enabled: false,
        disabledReason: 'Disabled by your administrator',
      });
    });

    it('extracts permissions with a fallback', () => {
      const extracted = extractPermissions(permissions, fallback);
      expect(extracted.canLaunchPipelineExecution).toEqual({
        enabled: false,
        disabledReason: 'u cannot',
      });

      // Does not end up with `fallback` value
      expect(extracted.canStopSensor).toEqual({
        enabled: true,
        disabledReason: '',
      });

      // Uses `fallback` value
      expect(extracted.canStartSchedule).toEqual({
        enabled: true,
        disabledReason: '',
      });

      // Falls back to base default permission
      expect(extracted.canReloadWorkspace).toEqual({
        enabled: false,
        disabledReason: 'Disabled by your administrator',
      });
    });
  });
});

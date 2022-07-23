import permissions from '../graphql/permissions.json';

import {EXPECTED_PERMISSIONS} from './Permissions';

describe('Permissions', () => {
  it('Client permissions match graphql permissions', () => {
    permissions.forEach(({permission}: {permission: any}) => {
      expect(permission in EXPECTED_PERMISSIONS).toBe(true);
    });
  });
});

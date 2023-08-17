import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {PermissionsProvider, usePermissionsForLocation} from '../../app/Permissions';
import {ChildProps, ReloadRepositoryLocationButton} from '../ReloadRepositoryLocationButton';
import {buildPermissionsQuery} from '../__fixtures__/ReloadRepositoryLocationButton.fixtures';

describe('ReloadRepositoryLocationButton', () => {
  const Test: React.FC<ChildProps> = (props) => {
    const {tryReload, hasReloadPermission} = props;
    const {loading} = usePermissionsForLocation(props.codeLocation);
    return (
      <div>
        <div>Loading permissions? {loading ? 'Yes' : 'No'}</div>
        <button onClick={tryReload} disabled={!hasReloadPermission}>
          Reload
        </button>
      </div>
    );
  };

  it('renders an disabled reload button if not permissioned', async () => {
    render(
      <MockedProvider mocks={[buildPermissionsQuery(false)]}>
        <PermissionsProvider>
          <ReloadRepositoryLocationButton location="foobar" ChildComponent={Test} />
        </PermissionsProvider>
      </MockedProvider>,
    );

    const button = screen.getByRole('button', {name: /reload/i});

    await waitFor(() => {
      expect(screen.queryByText(/loading permissions\? no/i)).not.toBeNull();
    });

    expect(button).toBeDisabled();
  });

  it('renders an enabled reload button if permissioned', async () => {
    render(
      <MockedProvider mocks={[buildPermissionsQuery(true)]}>
        <PermissionsProvider>
          <ReloadRepositoryLocationButton location="foobar" ChildComponent={Test} />
        </PermissionsProvider>
      </MockedProvider>,
    );

    const button = screen.getByRole('button', {name: /reload/i});

    await waitFor(() => {
      expect(screen.queryByText(/loading permissions\? no/i)).not.toBeNull();
    });

    expect(button).toBeEnabled();
  });
});

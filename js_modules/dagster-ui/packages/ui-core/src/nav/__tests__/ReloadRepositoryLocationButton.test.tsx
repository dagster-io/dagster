import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import {Suspense} from 'react';

import {PermissionsProvider, usePermissionsForLocation} from '../../app/Permissions';
import {TrackedSuspense} from '../../app/TrackedSuspense';
import {ChildProps, ReloadRepositoryLocationButton} from '../ReloadRepositoryLocationButton';
import {buildPermissionsQuery} from '../__fixtures__/ReloadRepositoryLocationButton.fixtures';

describe('ReloadRepositoryLocationButton', () => {
  const Test = (props: ChildProps) => {
    const {tryReload, hasReloadPermission} = props;

    function Component() {
      usePermissionsForLocation(props.codeLocation);
      return <div>Loading permissions? No</div>;
    }
    return (
      <div>
        <TrackedSuspense id="test" fallback={<div>Loading permissions? Yes</div>}>
          <Component />
        </TrackedSuspense>
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
          <Suspense>
            <ReloadRepositoryLocationButton location="foobar" ChildComponent={Test} />
          </Suspense>
        </PermissionsProvider>
      </MockedProvider>,
    );

    const button = await waitFor(() => screen.getByRole('button', {name: /reload/i}));

    await waitFor(() => {
      expect(screen.queryByText(/loading permissions\? no/i)).not.toBeNull();
    });

    expect(button).toBeDisabled();
  });

  it('renders an enabled reload button if permissioned', async () => {
    render(
      <MockedProvider mocks={[buildPermissionsQuery(true)]}>
        <PermissionsProvider>
          <Suspense>
            <ReloadRepositoryLocationButton location="foobar" ChildComponent={Test} />
          </Suspense>
        </PermissionsProvider>
      </MockedProvider>,
    );

    const button = await waitFor(() => screen.getByRole('button', {name: /reload/i}));

    await waitFor(() => {
      expect(screen.queryByText(/loading permissions\? no/i)).not.toBeNull();
    });

    expect(button).toBeEnabled();
  });
});

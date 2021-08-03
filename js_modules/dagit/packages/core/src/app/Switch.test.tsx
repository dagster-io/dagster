import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {PermissionsMap, usePermissions} from './Permissions';
import {Switch} from './Switch';
import {RenderConfig, RouteConfig} from './types';

describe('Switch', () => {
  const bazRoutes = [
    {
      path: '/baz/dorp',
      render: () => <div>Dorp</div>,
    },
    {
      path: '/baz/:id',
      render: (config: RenderConfig<{id: string}, PermissionsMap>) => (
        <div>{`Baz ${config.match.params.id}`}</div>
      ),
    },
    {
      path: '*',
      render: () => <div>Baz Fall</div>,
    },
  ];

  const gatedRoutes = [
    {
      path: '/gated/no',
      isAvailable: () => false,
      render: () => <div>Unlikely!</div>,
    },
    {
      path: '/gated/yes',
      isAvailable: () => true,
      render: () => <div>Welcome!</div>,
    },
    {
      path: '/gated/check',
      isAvailable: (permissions: PermissionsMap) => permissions.canReloadRepositoryLocation,
      render: () => <div>Welcome check!</div>,
    },
    {
      path: '*',
      render: () => <div>Gated fallback</div>,
    },
  ];

  const noFallthroughRoutes = [
    {
      path: '/no-fallthrough/skip',
      render: () => <div>Unlikely!</div>,
    },
  ];

  const routes = [
    {
      path: '/foo',
      render: () => <div>Foo</div>,
    },
    {
      path: '/bar',
      render: () => <div>Bar</div>,
    },
    {
      path: '/baz',
      routes: bazRoutes,
    },
    {
      path: '/gated',
      routes: gatedRoutes,
    },
    {
      path: '/no-fallthrough',
      routes: noFallthroughRoutes,
    },
    {
      path: '*',
      render: () => <div>Fallthrough</div>,
    },
  ];

  interface Props {
    routes: RouteConfig<any, PermissionsMap>[];
  }

  const Test: React.FC<Props> = ({routes}) => {
    const permissions = usePermissions();
    return <Switch permissions={permissions} routes={routes} />;
  };

  it('Finds the correct route at the top level', async () => {
    const routerProps = {
      initialEntries: ['/foo'],
    };

    render(
      <TestProvider routerProps={routerProps}>
        <Test routes={routes} />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/foo/i)).toBeVisible();
    });
  });

  it('Iterates until it finds the correct route', async () => {
    const routerProps = {
      initialEntries: ['/bar'],
    };

    render(
      <TestProvider routerProps={routerProps}>
        <Test routes={routes} />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/bar/i)).toBeVisible();
    });
  });

  describe('Subtree', () => {
    it('Steps into a route with a subtree of routes', async () => {
      const routerProps = {
        initialEntries: ['/baz'],
      };

      render(
        <TestProvider routerProps={routerProps}>
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/baz fall/i)).toBeVisible();
      });
    });

    it('Finds a subtree match', async () => {
      const routerProps = {
        initialEntries: ['/baz/dorp'],
      };

      render(
        <TestProvider routerProps={routerProps}>
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/^dorp$/i)).toBeVisible();
      });
    });

    it('Finds a subtree match with a path variable', async () => {
      const routerProps = {
        initialEntries: ['/baz/hello'],
      };

      render(
        <TestProvider routerProps={routerProps}>
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/baz hello/i)).toBeVisible();
      });
    });
  });

  describe('isAvailable', () => {
    it('Matches when `isAvailable` is true', async () => {
      const routerProps = {
        initialEntries: ['/gated/yes'],
      };

      render(
        <TestProvider routerProps={routerProps}>
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/welcome!/i)).toBeVisible();
      });
    });

    it('Rejects match when `isAvailable` is false', async () => {
      const routerProps = {
        initialEntries: ['/gated/no'],
      };

      render(
        <TestProvider routerProps={routerProps}>
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/gated fall/i)).toBeVisible();
      });
    });

    it('Checks permission value in `isAvailable`, acceptance', async () => {
      const routerProps = {
        initialEntries: ['/gated/check'],
      };

      render(
        <TestProvider routerProps={routerProps}>
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/welcome check/i)).toBeVisible();
      });
    });

    it('Checks permission value in `isAvailable`, rejection', async () => {
      const routerProps = {
        initialEntries: ['/gated/check'],
      };

      render(
        <TestProvider
          permissionOverrides={{reload_repository_location: false}}
          routerProps={routerProps}
        >
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/gated fallback/i)).toBeVisible();
      });
    });
  });

  describe('Route list with no fallthrough (404)', () => {
    it('ends up on a 404 if the route list has no `*` fallthrough', async () => {
      const routerProps = {
        initialEntries: ['/no-fallthrough/yikes'],
      };

      render(
        <TestProvider routerProps={routerProps}>
          <Test routes={routes} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.getByText(/404/i)).toBeVisible();
      });
    });
  });
});

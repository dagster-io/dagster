import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {RunStatus, buildRun} from '../../graphql/types';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {RunActionButtons} from '../RunActionButtons';
import {buildMockRootWorkspaceQuery} from '../__fixtures__/RunActionsMenu.fixtures';
import {RunPageFragment} from '../types/RunFragments.types';

describe('RunActionButtons', () => {
  const props = {
    selection: {
      keys: [],
      query: '',
    },
    graph: [],
    metadata: {
      firstLogAt: 0,
      mostRecentLogAt: 0,
      globalMarkers: [],
      steps: {},
    },
    onLaunch: jest.fn(),
  };

  const Test = ({run}: {run: RunPageFragment}) => {
    return (
      <MockedProvider mocks={buildMockRootWorkspaceQuery()}>
        <MemoryRouter>
          <WorkspaceProvider>
            <RunActionButtons {...props} run={run} />
          </WorkspaceProvider>
        </MemoryRouter>
      </MockedProvider>
    );
  };

  describe('`Terminate` button', () => {
    it('is visible for `STARTED` runs', async () => {
      const run = buildRun({status: RunStatus.STARTED});
      render(<Test run={run} />);
      expect(await screen.findByRole('button', {name: /terminate/i})).toBeVisible();
    });

    it('is visible for `STARTING` runs', async () => {
      const run = buildRun({status: RunStatus.STARTING});
      render(<Test run={run} />);
      expect(await screen.findByRole('button', {name: /terminate/i})).toBeVisible();
    });

    it('is NOT visible for `FAILURE` runs', async () => {
      const run = buildRun({status: RunStatus.FAILURE});
      render(<Test run={run} />);
      expect(await screen.findByRole('button', {name: /re-execute/i})).toBeVisible();
      expect(screen.queryByRole('button', {name: /terminate/i})).toBeNull();
    });

    it('is NOT visible for `CANCELED` runs', async () => {
      const run = buildRun({status: RunStatus.CANCELED});
      render(<Test run={run} />);
      expect(await screen.findByRole('button', {name: /re-execute/i})).toBeVisible();
      expect(screen.queryByRole('button', {name: /terminate/i})).toBeNull();
    });

    it('is NOT visible for `SUCCESS` runs', async () => {
      const run = buildRun({status: RunStatus.SUCCESS});
      render(<Test run={run} />);
      expect(await screen.findByRole('button', {name: /re-execute/i})).toBeVisible();
      expect(screen.queryByRole('button', {name: /terminate/i})).toBeNull();
    });
  });
});

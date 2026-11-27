import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {IsMobileContext} from '../../app/layout/IsMobileContext';
import {buildInstigationState, buildInstigationTick, buildRun} from '../../graphql/builders';
import {InstigationTickStatus, InstigationType} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {TICK_HISTORY_QUERY, TicksTable} from '../TickHistory';
import {TickHistoryQuery, TickHistoryQueryVariables} from '../types/TickHistory.types';

const ticksMock = buildQueryMock<TickHistoryQuery, TickHistoryQueryVariables>({
  query: TICK_HISTORY_QUERY,
  variableMatcher: () => true,
  data: {
    instigationStateOrError: buildInstigationState({
      instigationType: InstigationType.SENSOR,
      ticks: [1, 2].map((ii) =>
        buildInstigationTick({
          id: `tick-${ii}`,
          tickId: `${ii}`,
          status: InstigationTickStatus.SUCCESS,
          instigationType: InstigationType.SENSOR,
          timestamp: 1700000000 + ii,
          endTimestamp: 1700000010 + ii,
          cursor: `cursor-${ii}`,
          runIds: [`run-${ii}`],
          runs: [buildRun({id: `run-${ii}`})],
          dynamicPartitionsRequestResults: [],
        }),
      ),
    }),
  },
});

const renderTicksTable = (isMobile: boolean) =>
  render(
    <MemoryRouter>
      <MockedProvider mocks={[ticksMock]}>
        <IsMobileContext.Provider value={isMobile}>
          <TicksTable
            name="my_sensor"
            repoAddress={buildRepoAddress('repo', 'loc')}
            tickResultType="runs"
          />
        </IsMobileContext.Provider>
      </MockedProvider>
    </MemoryRouter>,
  );

describe('TicksTable', () => {
  it('renders ticks as grid rows on desktop', async () => {
    renderTicksTable(false);
    expect(await screen.findAllByRole('button', {name: 'View logs'})).toHaveLength(2);
    expect(screen.getByText('Cursor')).toBeVisible();
  });

  it('renders the same ticks as stacked items on mobile', async () => {
    renderTicksTable(true);
    expect(await screen.findAllByRole('button', {name: 'View logs'})).toHaveLength(2);
    expect(screen.queryByText('Cursor')).toBeNull();
    expect(screen.getAllByRole('button', {name: '1 run requested'})).toHaveLength(2);
  });
});

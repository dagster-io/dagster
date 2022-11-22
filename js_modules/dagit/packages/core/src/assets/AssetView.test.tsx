import {act, render, screen} from '@testing-library/react';
import faker from 'faker';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {TestProvider} from '../testing/TestProvider';

import {AssetView} from './AssetView';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../graph/asyncGraphLayout', () => ({}));

// This file must be mocked because useVirtualizer tries to create a ResizeObserver,
// and the component tree fails to mount.
jest.mock('./AssetPartitions', () => ({AssetPartitions: () => <div />}));

describe('AssetView', () => {
  const mocks = {
    AssetNode: () => ({
      partitionKeys: () => [...new Array(0)],
      partitionKeysByDimension: () => [...new Array(1)],
    }),
    Asset: () => ({
      assetMaterializations: () => [...new Array(1)],
      assetObservations: () => [...new Array(0)],
    }),
    MaterializationEvent: () => ({
      timestamp: () => '100',
    }),
    MetadataEntry: () => ({
      __typename: 'TextMetadataEntry',
      label: () => faker.random.word().toLocaleLowerCase(),
    }),
  };

  const Test = ({path}: {path: string}) => {
    return (
      <TestProvider apolloProps={{mocks}}>
        <MemoryRouter initialEntries={[path]}>
          <AssetView assetKey={{path: ['foo']}} />
        </MemoryRouter>
      </TestProvider>
    );
  };

  const MESSAGE = /this is a historical view of materializations as of \./i;

  describe('Historical view alert', () => {
    it('shows historical view alert if `asOf` is old', async () => {
      await act(async () => {
        render(<Test path="/foo?asOf=10" />);
      });
      expect(screen.queryByText(MESSAGE)).toBeVisible();
    });

    it('does not show historical view alert if `asOf` is past latest materialization', async () => {
      await act(async () => {
        render(<Test path="/foo?asOf=200" />);
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });

    it('does not show historical view alert if `asOf` is equal to latest materialization', async () => {
      await act(async () => {
        render(<Test path="/foo?asOf=100" />);
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });

    it('does not show historical view alert if no `asOf` is specified', async () => {
      await act(async () => {
        render(<Test path="/foo" />);
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });
  });
});

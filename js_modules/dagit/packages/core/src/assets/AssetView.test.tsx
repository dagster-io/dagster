import {render, screen, waitForElementToBeRemoved} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {TestProvider} from '../testing/TestProvider';

import {AssetView} from './AssetView';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../graph/asyncGraphLayout', () => ({}));

describe('AssetView', () => {
  const defaultMocks = {
    MaterializationEvent: () => ({
      timestamp: 100,
    }),
  };

  const Test = ({path}: {path: string}) => {
    return (
      <TestProvider apolloProps={{mocks: defaultMocks}}>
        <MemoryRouter initialEntries={[path]}>
          <AssetView assetKey={{path: ['foo']}} />
        </MemoryRouter>
      </TestProvider>
    );
  };

  const MESSAGE = /this is a historical view of materializations as of \./i;

  describe('Historical view alert', () => {
    it('shows historical view alert if `asOf` is old', async () => {
      render(<Test path="/foo?asOf=10" />);
      const spinner = screen.queryByTitle(/loading…/i);
      await waitForElementToBeRemoved(spinner);
      expect(screen.queryByText(MESSAGE)).toBeVisible();
    });

    it('does not show historical view alert if `asOf` is past latest materialization', async () => {
      render(<Test path="/foo?asOf=200" />);
      const spinner = screen.queryByTitle(/loading…/i);
      await waitForElementToBeRemoved(spinner);
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });

    it('does not show historical view alert if `asOf` is equal to latest materialization', async () => {
      render(<Test path="/foo?asOf=100" />);
      const spinner = screen.queryByTitle(/loading…/i);
      await waitForElementToBeRemoved(spinner);
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });

    it('does not show historical view alert if no `asOf` is specified', async () => {
      render(<Test path="/foo" />);
      const spinner = screen.queryByTitle(/loading…/i);
      await waitForElementToBeRemoved(spinner);
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });
  });
});

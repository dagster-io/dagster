import {screen} from '@testing-library/dom';
import {render} from '@testing-library/react';
import * as React from 'react';
import {act} from 'react-dom/test-utils';

import {TestProvider} from '../../testing/TestProvider';
import {VersionNumber} from '../VersionNumber';

describe('VersionNumber', () => {
  it('renders the version number', async () => {
    const mocks = {
      DagitQuery: () => ({
        version: '1.2.34',
      }),
    };

    await act(async () => {
      render(
        <TestProvider apolloProps={{mocks}}>
          <VersionNumber />
        </TestProvider>,
      );
    });

    expect(screen.getByText(/1\.2\.34/)).toBeVisible();
  });
});

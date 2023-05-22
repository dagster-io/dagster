import {screen} from '@testing-library/dom';
import {render} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../../testing/TestProvider';
import {VersionNumber} from '../VersionNumber';

describe('VersionNumber', () => {
  it('renders the version number', async () => {
    const mocks = {
      DagitQuery: () => ({
        version: '1.2.34',
      }),
    };

    render(
      <TestProvider apolloProps={{mocks}}>
        <VersionNumber />
      </TestProvider>,
    );

    expect(await screen.findByText(/1\.2\.34/)).toBeVisible();
  });
});

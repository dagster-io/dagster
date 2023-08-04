import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {screen} from '@testing-library/dom';
import {render} from '@testing-library/react';
import * as React from 'react';

import {VERSION_NUMBER_QUERY, VersionNumber} from '../VersionNumber';
import {VersionNumberQuery} from '../types/VersionNumber.types';

describe('VersionNumber', () => {
  it('renders the version number', async () => {
    const mock: MockedResponse<VersionNumberQuery> = {
      request: {
        query: VERSION_NUMBER_QUERY,
        variables: {},
      },
      result: {
        data: {
          __typename: 'Query',
          version: '1.2.34',
        },
      },
    };

    render(
      <MockedProvider mocks={[mock]}>
        <VersionNumber />
      </MockedProvider>,
    );

    expect(await screen.findByText(/1\.2\.34/)).toBeVisible();
  });
});

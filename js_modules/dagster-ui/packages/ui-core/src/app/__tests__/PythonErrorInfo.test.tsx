import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {GenericError, PythonErrorInfo} from '../PythonErrorInfo';
import {PythonErrorFragment} from '../types/PythonErrorFragment.types';

describe('PythonErrorInfo', () => {
  it('renders a real PythonErrorFragment', async () => {
    const error: PythonErrorFragment = {
      __typename: 'PythonError',
      message: 'lol oh no',
      stack: ['u have failed', 'rofl'],
      errorChain: [
        {
          __typename: 'ErrorChainLink',
          error: {
            __typename: 'PythonError',
            message: 'u wrote bad code',
            stack: ['problem here', 'whoops'],
          },
          isExplicitLink: true,
        },
        {
          __typename: 'ErrorChainLink',
          error: {
            __typename: 'PythonError',
            message: 'u wrote even worse code',
            stack: ['worse problem here', 'whoops'],
          },
          isExplicitLink: false,
        },
      ],
    };
    render(<PythonErrorInfo error={error} />);

    expect(screen.getByText(/lol oh no/i)).toBeVisible();
    expect(screen.getByText(/u wrote bad code/i)).toBeVisible();
    expect(screen.getByText(/u wrote even worse code/i)).toBeVisible();
    expect(
      screen.getByText(/The above exception was caused by the following exception:/i),
    ).toBeVisible();
    expect(
      screen.getByText(/The above exception occurred during handling of the following exception:/i),
    ).toBeVisible();
  });

  it('renders a generic error without errors', async () => {
    const error: GenericError = {
      message: 'failure all around',
    };
    render(<PythonErrorInfo error={error} />);

    expect(screen.queryByText(/failure all around/i)).toBeVisible();
  });
});

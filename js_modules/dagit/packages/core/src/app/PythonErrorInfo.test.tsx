import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {GenericError, PythonErrorInfo} from './PythonErrorInfo';
import {PythonErrorFragment} from './types/PythonErrorFragment';

describe('PythonErrorInfo', () => {
  it('renders a real PythonErrorFragment', async () => {
    const error: PythonErrorFragment = {
      __typename: 'PythonError',
      message: 'lol oh no',
      stack: ['u have failed', 'rofl'],
      causes: [
        {
          __typename: 'PythonError',
          message: 'u wrote bad code',
          stack: ['problem here', 'whoops'],
        },
      ],
    };
    render(<PythonErrorInfo error={error} />);

    expect(screen.getByText(/lol oh no/i)).toBeVisible();
    expect(screen.getByText(/u wrote bad code/i)).toBeVisible();
  });

  it('renders a generic error without errors', async () => {
    const error: GenericError = {
      message: 'failure all around',
    };
    render(<PythonErrorInfo error={error} />);

    expect(screen.queryByText(/failure all around/i)).toBeVisible();
  });
});

import {Button} from '@dagster-io/ui';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {act} from 'react-dom/test-utils';

import {CustomConfirmationProvider, useConfirmation} from './CustomConfirmationProvider';

describe('CustomConfirmationProvider', () => {
  const Test = () => {
    const [confirmed, setConfirmed] = React.useState(false);
    const confirm = useConfirmation();
    const onClick = async () => {
      await confirm({title: 'r u sure about this', description: 'it could be a bad idea'});
      setConfirmed(true);
    };
    return (
      <>
        <Button onClick={onClick}>Terminate</Button>
        <div>Confirmed? {String(confirmed)}</div>
      </>
    );
  };

  it('must not render a Dialog initially', async () => {
    render(
      <CustomConfirmationProvider>
        <Test />
      </CustomConfirmationProvider>,
    );

    expect(screen.queryByRole('button', {name: /cancel/i})).toBeNull();
  });

  it('must render a Dialog when `confirm` is executed', async () => {
    render(
      <CustomConfirmationProvider>
        <Test />
      </CustomConfirmationProvider>,
    );

    const button = screen.queryByRole('button', {name: /terminate/i}) as HTMLButtonElement;
    userEvent.click(button);

    expect(screen.queryByText(/r u sure about this/i)).toBeVisible();
  });

  it('must perform confirmation correctly', async () => {
    render(
      <CustomConfirmationProvider>
        <Test />
      </CustomConfirmationProvider>,
    );

    const button = screen.queryByRole('button', {name: /terminate/i}) as HTMLButtonElement;
    userEvent.click(button);

    const confirmationButton = screen.queryByRole('button', {
      name: /confirm/i,
    }) as HTMLButtonElement;

    // Resolves the promise.
    await act(async () => {
      userEvent.click(confirmationButton);
    });

    expect(screen.queryByText(/confirmed\? true/i)).toBeVisible();
  });

  it('must remove the confirmation Dialog from the DOM afterward', async () => {
    jest.useFakeTimers();

    render(
      <CustomConfirmationProvider>
        <Test />
      </CustomConfirmationProvider>,
    );

    const button = screen.queryByRole('button', {name: /terminate/i}) as HTMLButtonElement;
    userEvent.click(button);

    const confirmationButton = screen.queryByRole('button', {
      name: /confirm/i,
    }) as HTMLButtonElement;

    // Resolves the promise.
    await act(async () => {
      userEvent.click(confirmationButton);
    });

    expect(screen.queryByText(/confirmed\? true/i)).toBeVisible();

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    const dialogContainers = document.querySelectorAll('.bp3-dialog');
    expect(dialogContainers).toHaveLength(0);
  });
});

import {Button} from '@dagster-io/ui-components';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {useState} from 'react';
import {act} from 'react-dom/test-utils';

import {CustomConfirmationProvider, useConfirmation} from '../CustomConfirmationProvider';

describe('CustomConfirmationProvider', () => {
  const Test = () => {
    const [confirmed, setConfirmed] = useState(false);
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
    await userEvent.click(button);

    expect(screen.queryByText(/r u sure about this/i)).toBeVisible();
  });

  it('must perform confirmation correctly', async () => {
    render(
      <CustomConfirmationProvider>
        <Test />
      </CustomConfirmationProvider>,
    );

    const button = screen.queryByRole('button', {name: /terminate/i}) as HTMLButtonElement;
    await userEvent.click(button);

    const confirmationButton = screen.queryByRole('button', {
      name: /confirm/i,
    }) as HTMLButtonElement;

    // Resolves the promise.
    await userEvent.click(confirmationButton);

    expect(screen.queryByText(/confirmed\? true/i)).toBeVisible();
  });

  it('must remove the confirmation Dialog from the DOM afterward', async () => {
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    jest.useFakeTimers();

    render(
      <CustomConfirmationProvider>
        <Test />
      </CustomConfirmationProvider>,
    );

    const button = screen.queryByRole('button', {name: /terminate/i}) as HTMLButtonElement;
    await user.click(button);

    const confirmationButton = screen.queryByRole('button', {
      name: /confirm/i,
    }) as HTMLButtonElement;

    // Resolves the promise.
    await user.click(confirmationButton);

    await screen.findByText(/confirmed\? true/i);

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    await waitFor(() => {
      const dialogContainers = document.querySelectorAll('.bp5-dialog');
      expect(dialogContainers).toHaveLength(0);
    });
  });
});

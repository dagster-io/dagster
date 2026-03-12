import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {Button} from '../Button';
import {Dialog, DialogBody, DialogFooter, DialogHeader} from '../Dialog';
import {Tag} from '../Tag';

describe('Dialog', () => {
  it('renders title and body content when open', async () => {
    render(
      <Dialog isOpen onClose={jest.fn()} icon="layers" title="Start the process">
        <DialogBody>Body content</DialogBody>
        <DialogFooter>
          <Button intent="none">Cancel</Button>
          <Button intent="primary">Perform action</Button>
        </DialogFooter>
      </Dialog>,
    );

    expect(await screen.findByText('Start the process')).toBeVisible();
    expect(await screen.findByText('Body content')).toBeVisible();
    expect(await screen.findByRole('button', {name: /cancel/i})).toBeVisible();
    expect(await screen.findByRole('button', {name: /perform action/i})).toBeVisible();
  });

  it('does not render a close button in the header by default', async () => {
    render(
      <Dialog isOpen onClose={jest.fn()} icon="layers" title="Start the process">
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    await screen.findByText('Start the process');
    expect(screen.queryByRole('button', {name: /close/i})).not.toBeInTheDocument();
  });

  it('renders a close button in the header when isCloseButtonShown is set', async () => {
    render(
      <Dialog isOpen onClose={jest.fn()} icon="layers" title="Start the process" isCloseButtonShown>
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    expect(await screen.findByRole('button', {name: /close/i})).toBeVisible();
  });

  it('calls onClose when the header close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    render(
      <Dialog isOpen onClose={onClose} icon="layers" title="Start the process" isCloseButtonShown>
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    await user.click(await screen.findByRole('button', {name: /close/i}));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe('DialogHeader', () => {
  it('renders the label', async () => {
    render(
      <Dialog isOpen onClose={jest.fn()}>
        <DialogHeader icon="layers" label="Start the process" />
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    expect(await screen.findByText('Start the process')).toBeVisible();
  });

  it('does not render a close button by default', async () => {
    render(
      <Dialog isOpen onClose={jest.fn()}>
        <DialogHeader icon="layers" label="Start the process" />
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    await screen.findByText('Start the process');
    expect(screen.queryByRole('button', {name: /close/i})).not.toBeInTheDocument();
  });

  it('renders a close button when isCloseButtonShown is set', async () => {
    render(
      <Dialog isOpen onClose={jest.fn()}>
        <DialogHeader
          icon="layers"
          label="Start the process"
          isCloseButtonShown
          onClose={jest.fn()}
        />
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    expect(await screen.findByRole('button', {name: /close/i})).toBeVisible();
  });

  it('calls onClose when the close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    render(
      <Dialog isOpen onClose={jest.fn()}>
        <DialogHeader
          icon="layers"
          label="Start the process"
          isCloseButtonShown
          onClose={onClose}
        />
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    await user.click(await screen.findByRole('button', {name: /close/i}));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders right content when provided', async () => {
    render(
      <Dialog isOpen onClose={jest.fn()}>
        <DialogHeader
          icon="layers"
          label="Start the process"
          right={<Tag intent="primary">Beta</Tag>}
        />
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    expect(await screen.findByText('Start the process')).toBeVisible();
    expect(await screen.findByText('Beta')).toBeVisible();
  });

  it('renders right content alongside a close button when both are provided', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    render(
      <Dialog isOpen onClose={jest.fn()}>
        <DialogHeader
          icon="layers"
          label="Start the process"
          right={<Tag intent="primary">Beta</Tag>}
          isCloseButtonShown
          onClose={onClose}
        />
        <DialogBody>Body content</DialogBody>
      </Dialog>,
    );

    expect(await screen.findByText('Beta')).toBeVisible();
    expect(await screen.findByRole('button', {name: /close/i})).toBeVisible();
    await user.click(await screen.findByRole('button', {name: /close/i}));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {Button} from '../Button';
import {Tooltip} from '../Tooltip';

describe('Tooltip', () => {
  it('renders with a tooltip wrapper if `canShow` is true', async () => {
    const user = userEvent.setup();
    render(
      <Tooltip canShow content="Hello world">
        <Button>Lorem</Button>
      </Tooltip>,
    );

    const button = screen.queryByRole('button', {name: /lorem/i});
    expect(button).toBeInTheDocument();
    await user.hover(button as HTMLElement);
    expect(await screen.findByRole('tooltip', {name: /hello world/i})).toBeVisible();
  });

  it('does not render with a tooltip wrapper if `canShow` is false', async () => {
    render(
      <Tooltip canShow={false} content="Hello world">
        <Button>Lorem</Button>
      </Tooltip>,
    );

    const trigger = document.querySelector('[data-radix-tooltip-trigger]');
    expect(trigger).not.toBeInTheDocument();
    const button = screen.queryByRole('button', {name: /lorem/i});
    expect(button).toBeVisible();
  });
});

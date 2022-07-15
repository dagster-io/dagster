import {render, screen} from '@testing-library/react';
import * as React from 'react';

import {Button} from './Button';
import {Tooltip} from './Tooltip';

describe('Tooltip', () => {
  it('renders with a tooltip wrapper if `canShow` is true', async () => {
    render(
      <Tooltip canShow content="Hello world">
        <Button>Lorem</Button>
      </Tooltip>,
    );

    const wrapper = document.getElementsByClassName('bp3-popover2-target');
    expect(wrapper.length).toBe(1);
    const button = screen.queryByRole('button', {name: /lorem/i});
    expect(wrapper[0]!.contains(button)).toBe(true);
  });

  it('does not render with a tooltip wrapper if `canShow` is false', async () => {
    render(
      <Tooltip canShow={false} content="Hello world">
        <Button>Lorem</Button>
      </Tooltip>,
    );

    const wrapper = document.getElementsByClassName('bp3-popover2-target');
    expect(wrapper.length).toBe(0);
    const button = screen.queryByRole('button', {name: /lorem/i});
    expect(button).toBeVisible();
  });
});

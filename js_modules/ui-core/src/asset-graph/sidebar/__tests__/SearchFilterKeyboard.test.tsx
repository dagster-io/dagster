import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {SearchFilter} from '../SearchFilter';

describe('SearchFilter', () => {
  it('selects the matching result on Enter, with no event', async () => {
    const user = userEvent.setup();
    const onSelectValue = jest.fn();
    render(
      <SearchFilter
        values={[
          {label: 'orders', value: '["raw","orders"]'},
          {label: 'customers', value: '["raw","customers"]'},
        ]}
        onSelectValue={onSelectValue}
      />,
    );

    await user.type(screen.getByPlaceholderText('Jump to…'), 'cust{Enter}');

    // The explorer's select handlers must tolerate this missing event.
    expect(onSelectValue).toHaveBeenCalledWith(undefined, '["raw","customers"]');
  });
});

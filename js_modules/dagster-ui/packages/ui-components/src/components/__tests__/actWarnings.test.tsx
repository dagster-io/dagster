import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {useState} from 'react';

const Counter = () => {
  const [count, setCount] = useState(0);
  return (
    <>
      <button onClick={() => setCount((current) => current + 1)}>Increment</button>
      <div>Count: {count}</div>
    </>
  );
};

describe('Act warnings', () => {
  it('increments', async () => {
    const user = userEvent.setup();
    render(<Counter />);
    const button = await screen.findByRole('button');
    await user.click(button);
    await waitFor(() => expect(screen.getByText(/count: 1/i)).toBeVisible());
  });
});

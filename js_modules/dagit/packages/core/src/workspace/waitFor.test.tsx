import {act, render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

describe('waitFor', () => {
  describe('With TestProvider', () => {
    const Test = () => (
      <TestProvider>
        <div>Hello</div>
      </TestProvider>
    );

    it('does require `act` if not wrapped in `waitFor`', async () => {
      await act(async () => {
        render(<Test />);
      });
      expect(screen.getByText(/hello/i)).toBeVisible();
    });

    it('does not require `act` if wrapped in `waitFor`', async () => {
      render(<Test />);

      await waitFor(() => {
        expect(screen.getByText(/hello/i)).toBeVisible();
      });
    });
  });

  describe('Without TestProvider', () => {
    it('does not require `act` if your rendered stuff is already there', () => {
      const Test = () => <div>Hello</div>;
      render(<Test />);
      expect(screen.getByText(/hello/i)).toBeVisible();
    });

    describe('Rendering requires driving forward', () => {
      const Test = () => {
        const [value, setValue] = React.useState(0);
        React.useEffect(() => {
          const timer = setTimeout(() => {
            setValue((current) => current + 1);
          }, 0);
          return () => {
            clearTimeout(timer);
          };
        }, []);
        return <div>Hello {value}</div>;
      };

      it('does require `act` if you need to drive rendering forward', async () => {
        const {rerender} = render(<Test />);
        expect(screen.getByText(/hello 0/i)).toBeVisible();

        await act(async () => rerender(<Test />));
        expect(screen.getByText(/hello 1/i)).toBeVisible();
      });

      it('or it requires a `wait` utility call if you need to drive rendering forward', async () => {
        render(<Test />);
        expect(screen.getByText(/hello 0/i)).toBeVisible();

        await waitFor(() => {
          expect(screen.getByText(/hello 1/i)).toBeVisible();
        });
      });
    });
  });
});

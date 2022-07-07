import {act, render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {Route, Switch} from 'react-router-dom';

import {TestProvider} from '../testing/TestProvider';

import {AnalyticsContext, GenericAnalytics, useTrackEvent, useTrackPageView} from './analytics';

describe('Analytics', () => {
  const createMockAnalytics = () => ({
    page: jest.fn(),
    track: jest.fn(),
  });

  const Test: React.FC<{mockAnalytics: GenericAnalytics}> = ({children, mockAnalytics}) => {
    return <AnalyticsContext.Provider value={mockAnalytics}>{children}</AnalyticsContext.Provider>;
  };

  describe('Page view tracking', () => {
    const Page = () => {
      useTrackPageView();
      return <div>Hello</div>;
    };

    it('tracks page views', async () => {
      jest.useFakeTimers();
      const mockAnalytics = createMockAnalytics();

      await act(async () => {
        render(
          <TestProvider routerProps={{initialEntries: ['/foo/hello']}}>
            <Test mockAnalytics={mockAnalytics}>
              <Switch>
                <Route path="/foo/:bar?">
                  <Page />
                </Route>
              </Switch>
            </Test>
          </TestProvider>,
        );
      });

      jest.advanceTimersByTime(400);
      const {page} = mockAnalytics;
      expect(page).toHaveBeenCalledTimes(1);

      // Track both the react-router Route path and the actual location pathname
      expect(page.mock.calls[0][0]).toBe('/foo/:bar?');
      expect(page.mock.calls[0][1]).toBe('/foo/hello');
    });
  });

  describe('Event tracking', () => {
    const Page = () => {
      const trackEvent = useTrackEvent();
      const onClick = () => {
        trackEvent('userClick');
      };
      return <button onClick={onClick}>Hello</button>;
    };

    it('tracks events, e.g. button clicks', async () => {
      jest.useFakeTimers();
      const mockAnalytics = createMockAnalytics();

      await act(async () => {
        render(
          <TestProvider routerProps={{initialEntries: ['/foo/hello']}}>
            <Test mockAnalytics={mockAnalytics}>
              <Switch>
                <Route path="/foo/:bar?">
                  <Page />
                </Route>
              </Switch>
            </Test>
          </TestProvider>,
        );
      });

      const button = screen.getByRole('button');
      act(() => {
        userEvent.click(button);
      });

      const {track} = mockAnalytics;
      expect(track).toHaveBeenCalledTimes(1);

      // Track both the react-router Route path and the actual location pathname
      expect(track.mock.calls[0][0]).toBe('userClick');
      expect(track.mock.calls[0][1]).toEqual({path: '/foo/:bar?', specificPath: '/foo/hello'});
    });
  });

  describe('Overriding Analytics context value', () => {
    const Page = () => {
      useTrackPageView();
      return <div>Hello</div>;
    };

    it('tracks page views with overidding functions', async () => {
      jest.useFakeTimers();
      const mockAnalytics = createMockAnalytics();
      const overrideAnalytics = createMockAnalytics();

      await act(async () => {
        render(
          <TestProvider routerProps={{initialEntries: ['/foo/hello']}}>
            <Test mockAnalytics={mockAnalytics}>
              <Test mockAnalytics={overrideAnalytics}>
                <Switch>
                  <Route path="/foo/:bar?">
                    <Page />
                  </Route>
                </Switch>
              </Test>
            </Test>
          </TestProvider>,
        );
      });

      jest.advanceTimersByTime(400);
      expect(mockAnalytics.page).toHaveBeenCalledTimes(0);
      expect(overrideAnalytics.page).toHaveBeenCalledTimes(1);
    });
  });
});

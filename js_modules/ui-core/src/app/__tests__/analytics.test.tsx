import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {MemoryRouter, Switch} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {Route} from '../Route';
import {AnalyticsContext, GenericAnalytics, useTrackEvent, useTrackPageView} from '../analytics';

describe('Analytics', () => {
  const createMockAnalytics = () => ({
    page: jest.fn(),
    track: jest.fn(),
  });

  const Test = ({
    children,
    mockAnalytics,
  }: {
    mockAnalytics: GenericAnalytics;
    children: React.ReactNode;
  }) => {
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

      render(
        <RecoilRoot>
          <MemoryRouter initialEntries={['/foo/hello']}>
            <Test mockAnalytics={mockAnalytics}>
              <Switch>
                <Route path="/foo/:bar?">
                  <Page />
                </Route>
              </Switch>
            </Test>
          </MemoryRouter>
        </RecoilRoot>,
      );

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
        trackEvent('thingClick');
      };
      return <button onClick={onClick}>Hello</button>;
    };

    it('tracks events, e.g. button clicks', async () => {
      const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
      jest.useFakeTimers();
      const mockAnalytics = createMockAnalytics();

      render(
        <RecoilRoot>
          <MemoryRouter initialEntries={['/foo/hello']}>
            <Test mockAnalytics={mockAnalytics}>
              <Switch>
                <Route path="/foo/:bar?">
                  <Page />
                </Route>
              </Switch>
            </Test>
          </MemoryRouter>
        </RecoilRoot>,
      );

      const button = screen.getByRole('button');
      await user.click(button);

      const {track} = mockAnalytics;
      expect(track).toHaveBeenCalledTimes(1);

      // Track both the react-router Route path and the actual location pathname
      expect(track.mock.calls[0][0]).toBe('thingClick');
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

      render(
        <RecoilRoot>
          <MemoryRouter initialEntries={['/foo/hello']}>
            <Test mockAnalytics={mockAnalytics}>
              <Test mockAnalytics={overrideAnalytics}>
                <Switch>
                  <Route path="/foo/:bar?">
                    <Page />
                  </Route>
                </Switch>
              </Test>
            </Test>
          </MemoryRouter>
        </RecoilRoot>,
      );

      jest.advanceTimersByTime(400);
      await waitFor(() => {
        expect(mockAnalytics.page).toHaveBeenCalledTimes(0);
        expect(overrideAnalytics.page).toHaveBeenCalledTimes(1);
      });
    });
  });
});

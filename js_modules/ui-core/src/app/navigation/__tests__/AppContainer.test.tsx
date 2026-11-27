import {act, render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {useEffect} from 'react';
import {MemoryRouter, Switch, useHistory} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {LayoutProvider} from '../../LayoutProvider';
import {Route} from '../../Route';
import {LayoutMode} from '../../layout/LayoutMode';
import {LayoutModeProvider} from '../../layout/LayoutModeProvider';
import {AppContainer} from '../AppContainer';
import {NavCollapseProvider} from '../NavCollapseProvider';

beforeAll(() => {
  // jsdom has no matchMedia; LayoutProvider only needs a non-matching stub.
  window.matchMedia = () =>
    ({matches: false, addEventListener: () => {}, removeEventListener: () => {}}) as any;
});

let history: ReturnType<typeof useHistory> | null = null;
const CaptureHistory = () => {
  history = useHistory();
  return null;
};

const mounts: string[] = [];
const Page = ({name}: {name: string}) => {
  useEffect(() => {
    mounts.push(name);
  }, [name]);
  return <div>{name} page</div>;
};

const renderApp = (mode: LayoutMode, path: string) =>
  render(
    <RecoilRoot>
      <LayoutModeProvider mode={mode}>
        <MemoryRouter initialEntries={[path]}>
          <CaptureHistory />
          <LayoutProvider>
            <NavCollapseProvider>
              <AppContainer topGroups={[]} bottomGroups={[]}>
                <Switch>
                  <Route path="/runs" mobile="supported">
                    <Page name="runs" />
                  </Route>
                  <Route path="/graph">
                    <Page name="graph" />
                  </Route>
                </Switch>
              </AppContainer>
            </NavCollapseProvider>
          </LayoutProvider>
        </MemoryRouter>
      </LayoutModeProvider>
    </RecoilRoot>,
  );

describe('AppContainer', () => {
  beforeEach(() => {
    mounts.length = 0;
  });

  it('renders the desktop navigation on desktop', () => {
    renderApp('desktop', '/runs');
    expect(screen.queryByLabelText('Open navigation')).toBeNull();
    expect(screen.getByText('runs page')).toBeVisible();
  });

  it('renders the mobile layout for a supported route without remounting the page', () => {
    renderApp('mobile', '/runs');
    expect(screen.getByLabelText('Open navigation')).toBeVisible();
    expect(screen.queryByText(/optimized for mobile/)).toBeNull();
    expect(mounts).toEqual(['runs']);
  });

  it('renders the desktop navigation with a banner for an unsupported route', () => {
    renderApp('mobile', '/graph');
    expect(screen.queryByLabelText('Open navigation')).toBeNull();
    expect(screen.getByText(/optimized for mobile/)).toBeVisible();
    expect(mounts).toEqual(['graph']);
  });

  it('switches layouts on navigation without remounting pages', () => {
    renderApp('mobile', '/runs');
    act(() => {
      history?.push('/graph');
    });
    expect(screen.getByText(/optimized for mobile/)).toBeVisible();
    act(() => {
      history?.push('/runs');
    });
    expect(screen.getByLabelText('Open navigation')).toBeVisible();
    expect(mounts).toEqual(['runs', 'graph', 'runs']);
  });

  it('opens and closes the drawer', async () => {
    const user = userEvent.setup();
    renderApp('mobile', '/runs');
    const dialog = screen.getByRole('dialog', {hidden: true});
    expect(dialog.parentElement).toHaveAttribute('aria-hidden', 'true');

    await user.click(screen.getByLabelText('Open navigation'));
    expect(dialog.parentElement).toHaveAttribute('aria-hidden', 'false');

    await user.keyboard('{Escape}');
    expect(dialog.parentElement).toHaveAttribute('aria-hidden', 'true');
  });

  it('leaves the drawer open when an overlay inside it consumes Escape', async () => {
    const user = userEvent.setup();
    renderApp('mobile', '/runs');
    const dialog = screen.getByRole('dialog', {hidden: true});
    await user.click(screen.getByLabelText('Open navigation'));
    expect(dialog.parentElement).toHaveAttribute('aria-hidden', 'false');

    // Stands in for a popover or dialog closing itself on Escape.
    const consumeEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
      }
    };
    document.addEventListener('keydown', consumeEscape, {capture: true});
    await user.keyboard('{Escape}');
    expect(dialog.parentElement).toHaveAttribute('aria-hidden', 'false');

    document.removeEventListener('keydown', consumeEscape, {capture: true});
    await user.keyboard('{Escape}');
    expect(dialog.parentElement).toHaveAttribute('aria-hidden', 'true');
  });
});

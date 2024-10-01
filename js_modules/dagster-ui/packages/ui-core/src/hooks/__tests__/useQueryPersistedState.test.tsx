import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {useCallback, useMemo} from 'react';
import {MemoryRouter} from 'react-router-dom';

import {Route} from '../../app/Route';
import {useQueryPersistedState} from '../useQueryPersistedState';

const Test = ({options}: {options: Parameters<typeof useQueryPersistedState>[0]}) => {
  const [query, setQuery] = useQueryPersistedState(options);
  return <div onClick={() => setQuery('Navigated')}>{`[${query}]`}</div>;
};

describe('useQueryPersistedState', () => {
  it('populates state from the query string', async () => {
    render(
      <MemoryRouter initialEntries={['/page?q=c']}>
        <Test options={{queryKey: 'q', defaults: {q: 'a'}}} />
      </MemoryRouter>,
    );
    expect(await screen.findByText(`[c]`)).toBeVisible();
  });

  it('populates from defaults if query params are not present', async () => {
    render(
      <MemoryRouter initialEntries={['/page']}>
        <Test options={{queryKey: 'q', defaults: {q: 'a'}}} />
      </MemoryRouter>,
    );
    expect(await screen.findByText(`[a]`)).toBeVisible();
  });

  it('populates with undefined values if defaults are not provided and query params are not present', async () => {
    render(
      <MemoryRouter initialEntries={['/page']}>
        <Test options={{queryKey: 'q'}} />
      </MemoryRouter>,
    );
    expect(await screen.findByText(`[undefined]`)).toBeVisible();
  });

  it('updates the URL query string when its exposed setter is called', async () => {
    // from https://reactrouter.com/web/guides/testing/checking-location-in-tests
    let querySearch: string | undefined;

    render(
      <MemoryRouter initialEntries={['/page?q=B']}>
        <Test options={{queryKey: 'q'}} />;
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(querySearch).toEqual('?q=B');
    });

    await userEvent.click(screen.getByText(`[B]`));

    expect(screen.getByText(`[Navigated]`)).toBeVisible();
    expect(querySearch).toEqual('?q=Navigated');
  });

  it('ignores and preserves other params present in the query string', async () => {
    // from https://reactrouter.com/web/guides/testing/checking-location-in-tests
    let querySearch: string | undefined;
    render(
      <MemoryRouter initialEntries={['/page?q=B&cursor=basdasd&limit=100']}>
        <Test options={{queryKey: 'q'}} />;
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`[B]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?q=Navigated&cursor=basdasd&limit=100');
    });
  });

  it('omits query params when their values are set to the default', async () => {
    // from https://reactrouter.com/web/guides/testing/checking-location-in-tests
    let querySearch: string | undefined;

    render(
      <MemoryRouter initialEntries={['/page?q=B&cursor=basdasd&limit=100']}>
        <Test options={{queryKey: 'q', defaults: {q: 'Navigated'}}} />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`[B]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?cursor=basdasd&limit=100');
    });
  });

  it('can coexist with other instances of the same hook', async () => {
    let querySearch: string | undefined;

    render(
      <MemoryRouter initialEntries={['/page?param1=A1&param2=A2']}>
        <Test options={{queryKey: 'param1'}} />
        <Test options={{queryKey: 'param2'}} />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(querySearch).toEqual('?param1=A1&param2=A2');
    });
    await userEvent.click(screen.getByText(`[A1]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?param1=Navigated&param2=A2');
    });
    await userEvent.click(screen.getByText(`[A2]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?param1=Navigated&param2=Navigated');
    });
    expect(screen.queryAllByText(`[Navigated]`).length).toEqual(2);
  });

  it('can coexist, even if you errantly retain the setter (just like setState)', async () => {
    const TestWithBug = () => {
      const [word, setWord] = useQueryPersistedState({queryKey: 'word'});
      const onCapturedForever = useCallback(() => {
        setWord('world');
        // This is an intentional user error
        // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);
      return <div onClick={onCapturedForever}>{`[${word}]`}</div>;
    };

    let querySearch: string | undefined;

    render(
      <MemoryRouter initialEntries={['/page?word=hello&param1=A']}>
        <Test options={{queryKey: 'param1'}} />
        <TestWithBug />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`[A]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?word=hello&param1=Navigated');
    });
    await userEvent.click(screen.getByText(`[hello]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?word=world&param1=Navigated'); // would reset param1=A in case of bug
    });
  });

  it('can be used to represent arbitrary state shapes via custom encode/decode methods', async () => {
    const TestEncoding = () => {
      const [items, setItems] = useQueryPersistedState<string[]>({
        encode: (items) => ({value: items.join(',')}),
        decode: (q) => q.value.split(',').filter(Boolean),
        defaults: {value: ''},
      });
      return (
        <div onClick={() => setItems([...items, `Added${items.length}`])}>
          {JSON.stringify(items)}
        </div>
      );
    };

    let querySearch: string | undefined;

    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestEncoding />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`[]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?value=Added0');
    });
    await userEvent.click(screen.getByText(`["Added0"]`));
    await userEvent.click(screen.getByText(`["Added0","Added1"]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?value=Added0%2CAdded1%2CAdded2');
    });
  });

  it('can be used to represent objects with optional / non-optional keys', async () => {
    const TestWithObject = () => {
      const [filters, setFilters] = useQueryPersistedState<{
        pipeline?: string;
        solid?: string;
        view: 'grid' | 'list';
      }>({
        defaults: {view: 'grid'},
      });
      return (
        <div onClick={() => setFilters({...filters, pipeline: 'my_pipeline'})}>
          {JSON.stringify(filters)}
        </div>
      );
    };

    let querySearch: string | undefined;
    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestWithObject />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`{"view":"grid"}`));
    await userEvent.click(screen.getByText(`{"view":"grid","pipeline":"my_pipeline"}`));
    expect(querySearch).toEqual('?pipeline=my_pipeline');
  });

  it('automatically coerces true/false if no encode/decode methods are provided', async () => {
    const TestWithObject = () => {
      const [filters, setFilters] = useQueryPersistedState<{
        enableA?: boolean;
        enableB?: boolean;
      }>({
        defaults: {enableA: true, enableB: false},
      });
      return (
        <div onClick={() => setFilters({enableA: !filters.enableA, enableB: !filters.enableB})}>
          {JSON.stringify(filters)}
        </div>
      );
    };
    let querySearch: string | undefined;
    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestWithObject />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`{"enableA":true,"enableB":false}`));
    await waitFor(() => {
      expect(querySearch).toEqual('?enableA=false&enableB=true');
    });
    await userEvent.click(screen.getByText(`{"enableA":false,"enableB":true}`));
    await waitFor(() => {
      expect(querySearch).toEqual('');
    });
  });

  it('emits the same setFilters on each render if memoized options are provided, matching React.useState', async () => {
    let firstSetFunction: (v: any) => void;

    const TestWithObject = () => {
      const [_, setFilters] = useQueryPersistedState<{isOn: boolean}>(
        useMemo(
          () => ({
            encode: ({isOn}) => ({isOn: isOn ? 'yes' : 'no'}),
            decode: (qs) => ({isOn: qs.isOn === 'yes' ? true : false}),
          }),
          [],
        ),
      );

      if (!firstSetFunction) {
        firstSetFunction = setFilters;
      }

      return (
        <div onClick={() => setFilters({isOn: true})}>
          {`Functions Same: ${firstSetFunction === setFilters}`}
        </div>
      );
    };

    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestWithObject />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`Functions Same: true`));
    expect(screen.getByText(`Functions Same: true`)).toBeVisible();
    await userEvent.click(screen.getByText(`Functions Same: true`));
    expect(screen.getByText(`Functions Same: true`)).toBeVisible();
  });

  it('correctly encodes arrays, using bracket syntax', async () => {
    const TestArray = () => {
      const [state, setState] = useQueryPersistedState<{value: string[]}>({defaults: {value: []}});
      return (
        <div onClick={() => setState({value: [...state.value, `Added${state.value.length}`]})}>
          {JSON.stringify(state.value)}
        </div>
      );
    };

    let querySearch: string | undefined;
    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestArray />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`[]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?value%5B%5D=Added0');
    });
    await userEvent.click(screen.getByText(`["Added0"]`));
    await userEvent.click(screen.getByText(`["Added0","Added1"]`));
    await waitFor(() => {
      expect(querySearch).toEqual('?value%5B%5D=Added0&value%5B%5D=Added1&value%5B%5D=Added2');
    });
  });

  it('correctly encodes arrays alongside other values, using bracket syntax', async () => {
    const TestArray = () => {
      const [state, setState] = useQueryPersistedState<{hello: boolean; items: string[]}>({
        defaults: {hello: false, items: []},
      });
      return (
        <div
          onClick={() =>
            setState({hello: true, items: [...state.items, `Added${state.items.length}`]})
          }
        >
          {JSON.stringify(state)}
        </div>
      );
    };

    let querySearch: any;

    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestArray />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText(`{"hello":false,"items":[]}`));

    await waitFor(() => {
      expect(querySearch).toEqual('?hello=true&items%5B%5D=Added0');
    });
    await userEvent.click(screen.getByText(`{"hello":true,"items":["Added0"]}`));
    await userEvent.click(screen.getByText(`{"hello":true,"items":["Added0","Added1"]}`));

    await waitFor(() => {
      expect(querySearch).toEqual(
        '?hello=true&items%5B%5D=Added0&items%5B%5D=Added1&items%5B%5D=Added2',
      );
    });
  });
});

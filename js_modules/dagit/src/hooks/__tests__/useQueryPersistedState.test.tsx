import {render, screen} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter, Route} from 'react-router-dom';

import {useQueryPersistedState} from 'src/hooks/useQueryPersistedState';

const Test: React.FunctionComponent<{options: Parameters<typeof useQueryPersistedState>[0]}> = ({
  options,
}) => {
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
    expect(screen.getByText(`[c]`)).toBeVisible();
  });

  it('populates from defaults if query params are not present', async () => {
    render(
      <MemoryRouter initialEntries={['/page']}>
        <Test options={{queryKey: 'q', defaults: {q: 'a'}}} />
      </MemoryRouter>,
    );
    expect(screen.getByText(`[a]`)).toBeVisible();
  });

  it('populates with undefined values if defaults are not provided and query params are not present', async () => {
    render(
      <MemoryRouter initialEntries={['/page']}>
        <Test options={{queryKey: 'q'}} />
      </MemoryRouter>,
    );
    expect(screen.getByText(`[undefined]`)).toBeVisible();
  });

  it('updates the URL query string when its exposed setter is called', async () => {
    // from https://reactrouter.com/web/guides/testing/checking-location-in-tests
    let querySearch;
    render(
      <MemoryRouter initialEntries={['/page?q=B']}>
        <Test options={{queryKey: 'q'}} />;
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );
    expect(querySearch).toEqual('?q=B');

    await screen.getByText(`[B]`).click();

    expect(screen.getByText(`[Navigated]`)).toBeVisible();
    expect(querySearch).toEqual('?q=Navigated');
  });

  it('ignores and preserves other params present in the query string', async () => {
    // from https://reactrouter.com/web/guides/testing/checking-location-in-tests
    let querySearch;
    render(
      <MemoryRouter initialEntries={['/page?q=B&cursor=basdasd&limit=100']}>
        <Test options={{queryKey: 'q'}} />;
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );
    await screen.getByText(`[B]`).click();
    expect(querySearch).toEqual('?cursor=basdasd&limit=100&q=Navigated');
  });

  it('omits query params when their values are set to the default', async () => {
    // from https://reactrouter.com/web/guides/testing/checking-location-in-tests
    let querySearch;
    render(
      <MemoryRouter initialEntries={['/page?q=B&cursor=basdasd&limit=100']}>
        <Test options={{queryKey: 'q', defaults: {q: 'Navigated'}}} />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );
    await screen.getByText(`[B]`).click();
    expect(querySearch).toEqual('?cursor=basdasd&limit=100');
  });

  it('can coexist with other instances of the same hook', async () => {
    let querySearch;
    render(
      <MemoryRouter initialEntries={['/page?param1=A1&param2=A2']}>
        <Test options={{queryKey: 'param1'}} />
        <Test options={{queryKey: 'param2'}} />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    expect(querySearch).toEqual('?param1=A1&param2=A2');
    await screen.getByText(`[A1]`).click();
    expect(querySearch).toEqual('?param1=Navigated&param2=A2');
    await screen.getByText(`[A2]`).click();
    expect(querySearch).toEqual('?param1=Navigated&param2=Navigated');
    expect(screen.queryAllByText(`[Navigated]`).length).toEqual(2);
  });

  it('can coexist, even if you errantly retain the setter (just like setState)', async () => {
    const TestWithBug: React.FunctionComponent = () => {
      const [word, setWord] = useQueryPersistedState({queryKey: 'word'});
      const onCapturedForever = React.useCallback(() => {
        setWord('world');
        // This is an intentional user error
        // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);
      return <div onClick={onCapturedForever}>{`[${word}]`}</div>;
    };

    let querySearch;
    render(
      <MemoryRouter initialEntries={['/page?word=hello&param1=A']}>
        <Test options={{queryKey: 'param1'}} />
        <TestWithBug />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await screen.getByText(`[A]`).click();
    expect(querySearch).toEqual('?param1=Navigated&word=hello');
    await screen.getByText(`[hello]`).click();
    expect(querySearch).toEqual('?param1=Navigated&word=world'); // would reset param1=A in case of bug
  });

  it('can be used to represent arbitrary state shapes via custom encode/decode methods', async () => {
    const TestEncoding: React.FunctionComponent = () => {
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
    let querySearch;
    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestEncoding />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await screen.getByText(`[]`).click();
    expect(querySearch).toEqual('?value=Added0');
    await screen.getByText(`["Added0"]`).click();
    await screen.getByText(`["Added0","Added1"]`).click();
    expect(querySearch).toEqual('?value=Added0%2CAdded1%2CAdded2');
  });

  it('can be used to represent objects with optional / non-optional keys', async () => {
    const TestWithObject: React.FunctionComponent = () => {
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
    let querySearch;
    render(
      <MemoryRouter initialEntries={['/page']}>
        <TestWithObject />
        <Route path="*" render={({location}) => (querySearch = location.search) && <span />} />
      </MemoryRouter>,
    );

    await screen.getByText(`{"view":"grid"}`).click();
    await screen.getByText(`{"view":"grid","pipeline":"my_pipeline"}`).click();
    expect(querySearch).toEqual('?pipeline=my_pipeline');
  });
});

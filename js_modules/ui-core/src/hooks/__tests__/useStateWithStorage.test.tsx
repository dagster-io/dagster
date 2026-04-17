import {act, renderHook} from '@testing-library/react';

import {useStateWithStorage} from '../useStateWithStorage';

describe('useStateWithStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('does not evict unrelated localStorage keys during successful writes', () => {
    const unrelatedEntries = Array.from({length: 51}, (_, index) => [
      `persisted-key-${index}`,
      index,
    ]);
    localStorage.setItem('__dagster_storage_lru__', JSON.stringify(unrelatedEntries));
    localStorage.setItem('persisted-key-0', JSON.stringify({keep: true}));

    const {result} = renderHook(() => useStateWithStorage('target-key', (json: any) => json ?? {}));

    act(() => {
      result.current[1]({saved: true});
    });

    expect(JSON.parse(localStorage.getItem('persisted-key-0') || 'null')).toEqual({keep: true});
    expect(JSON.parse(localStorage.getItem('target-key') || 'null')).toEqual({saved: true});
  });
});

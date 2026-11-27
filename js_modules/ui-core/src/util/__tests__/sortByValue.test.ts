import {sortByValue} from '../sortByValue';

describe('sortByValue', () => {
  const items = [{name: 'b'}, {name: 'c'}, {name: 'a'}];
  const byName = (a: string, b: string) => a.localeCompare(b);

  it('sorts by the computed value without mutating the input', () => {
    expect(sortByValue(items, (item) => item.name, byName).map((i) => i.name)).toEqual([
      'a',
      'b',
      'c',
    ]);
    expect(items.map((i) => i.name)).toEqual(['b', 'c', 'a']);
  });

  it('computes each value once', () => {
    const valueFor = jest.fn((item: {name: string}) => item.name);
    sortByValue(items, valueFor, byName);
    expect(valueFor).toHaveBeenCalledTimes(items.length);
  });

  it('keeps the input order for equal values', () => {
    const tied = [
      {name: 'x', id: 1},
      {name: 'x', id: 2},
      {name: 'a', id: 3},
    ];
    expect(sortByValue(tied, (item) => item.name, byName).map((i) => i.id)).toEqual([3, 1, 2]);
  });
});

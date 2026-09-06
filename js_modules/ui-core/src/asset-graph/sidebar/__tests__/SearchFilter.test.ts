import {ambiguousLabelsIn} from '../SearchFilter';

// Note: the rendering of these labels is covered by the
// `Asset Graph/Sidebar SearchFilter` stories rather than a render test — the
// Suggest menu is virtualized and renders no rows under jsdom.
describe('ambiguousLabelsIn', () => {
  it('returns nothing when every label is unique', () => {
    expect(ambiguousLabelsIn([{label: 'orders'}, {label: 'customers'}])).toEqual(new Set());
  });

  it('returns nothing for an empty list', () => {
    expect(ambiguousLabelsIn([])).toEqual(new Set());
  });

  it('reports a label shared by two entries', () => {
    expect(ambiguousLabelsIn([{label: 'orders'}, {label: 'orders'}])).toEqual(new Set(['orders']));
  });

  it('reports only the shared labels, leaving unique ones out', () => {
    expect(
      ambiguousLabelsIn([
        {label: 'orders'},
        {label: 'orders'},
        {label: 'inventory'},
        {label: 'customers'},
        {label: 'customers'},
      ]),
    ).toEqual(new Set(['orders', 'customers']));
  });

  it('reports a label shared by more than two entries once', () => {
    expect(ambiguousLabelsIn([{label: 'orders'}, {label: 'orders'}, {label: 'orders'}])).toEqual(
      new Set(['orders']),
    );
  });

  it('treats labels differing only in case as distinct', () => {
    // The menu renders them differently, so there is nothing to disambiguate.
    expect(ambiguousLabelsIn([{label: 'Orders'}, {label: 'orders'}])).toEqual(new Set());
  });
});

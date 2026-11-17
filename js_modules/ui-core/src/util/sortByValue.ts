/**
 * Returns a sorted copy of `items`, calling `valueFor` once per item rather than twice per
 * comparison. Use it when the sort value is built (e.g. a display name or asset token), since
 * a comparator that builds strings allocates O(n log n) of them.
 */
export function sortByValue<T, V>(
  items: readonly T[],
  valueFor: (item: T) => V,
  compare: (a: V, b: V) => number,
): T[] {
  return items
    .map((item) => ({item, value: valueFor(item)}))
    .sort((a, b) => compare(a.value, b.value))
    .map(({item}) => item);
}

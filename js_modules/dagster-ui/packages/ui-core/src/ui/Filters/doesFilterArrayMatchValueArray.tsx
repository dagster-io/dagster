import isEqual from 'lodash/isEqual';

// This function checks if every element in `filterArray` has at least one match in `valueArray` based on the provided `isMatch` comparison function.
// - `filterArray`: The array containing elements to be matched.
// - `valueArray`: The array to search for matches.
// - `isMatch`: A custom comparator function (defaults to deep equality using `lodash/isEqual`).
// Returns `false` if `filterArray` is non-empty and `valueArray` is empty (no matches possible).
// Otherwise, checks if all elements in `filterArray` have at least one corresponding match in `valueArray`.
// Uses `Array.prototype.some()` to verify if any `filterArray` element lacks a match and returns `false` in such cases.
export function doesFilterArrayMatchValueArray<T, V>(
  filterArray: T[],
  valueArray: V[],
  isMatch: (value1: T, value2: V) => boolean = (val1, val2) => {
    return isEqual(val1, val2);
  },
) {
  if (filterArray.length && !valueArray.length) {
    return false;
  }
  return !filterArray.some(
    (filterTag) =>
      // If no asset tags match this filter tag return true
      !valueArray.find((value) => isMatch(filterTag, value)),
  );
}

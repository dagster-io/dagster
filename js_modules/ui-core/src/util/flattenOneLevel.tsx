/**
 * Flattens a two-dimensional array into a one-dimensional array.
 *
 * @param nodeChunks - The two-dimensional array to flatten.
 * @returns The flattened one-dimensional array.
 */
// https://jsbench.me/o8kqzo8olz/1
export function flattenOneLevel<T>(arrays: T[][]) {
  return ([] as T[]).concat(...arrays);
}

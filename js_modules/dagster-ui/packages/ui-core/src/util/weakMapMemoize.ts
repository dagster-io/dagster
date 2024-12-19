type AnyFunction = (...args: any[]) => any;

function isObject(value: any): value is object {
  return value !== null && (typeof value === 'object' || typeof value === 'function');
}

/**
 * Interface representing a cache node that holds both a Map for primitive keys
 * and a WeakMap for object keys.
 */
interface CacheNode {
  map: Map<any, CacheNode>;
  weakMap: WeakMap<object, CacheNode>;
  result?: any;
}

/**
 * Memoizes a function using nested Maps and WeakMaps based on the arguments.
 * Handles both primitive and object arguments.
 * @param fn - The function to memoize.
 * @returns A memoized version of the function.
 */
export function weakMapMemoize<T extends AnyFunction>(fn: T): T {
  // Initialize the root cache node
  const cacheRoot: CacheNode = {
    map: new Map(),
    weakMap: new WeakMap(),
  };

  return function memoizedFunction(this: any, ...args: any[]) {
    let currentCache = cacheRoot;

    for (let i = 0; i < args.length; i++) {
      const arg = args[i];

      if (isObject(arg)) {
        // Use WeakMap for object keys
        if (!currentCache.weakMap.has(arg)) {
          currentCache.weakMap.set(arg, {
            map: new Map(),
            weakMap: new WeakMap(),
          });
        }
        currentCache = currentCache.weakMap.get(arg)!;
      } else {
        // Use Map for primitive keys
        if (!currentCache.map.has(arg)) {
          currentCache.map.set(arg, {
            map: new Map(),
            weakMap: new WeakMap(),
          });
        }
        currentCache = currentCache.map.get(arg)!;
      }
    }

    // After traversing all arguments, check if the result is cached
    if ('result' in currentCache) {
      return currentCache.result;
    }
    // Compute the result and cache it
    const result = fn.apply(this, args);
    currentCache.result = result;
    return result;
  } as T;
}

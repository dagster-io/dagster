import LRU from 'lru-cache';

type AnyFunction = (...args: any[]) => any;

interface WeakMapMemoizeOptions {
  maxEntries?: number; // Optional limit for cached entries
}

interface CacheNode {
  map: Map<any, CacheNode>;
  weakMap: WeakMap<object, CacheNode>;
  result?: any;
  lruKey?: any; // Reference to the key in the LRU cache
}

/**
 * Determines if a value is a non-null object or function.
 * @param value - The value to check.
 * @returns True if the value is a non-null object or function, false otherwise.
 */
function isObject(value: any): value is object {
  return value !== null && (typeof value === 'object' || typeof value === 'function');
}

/**
 * Memoizes a function using nested Maps and WeakMaps based on the arguments.
 * Optionally limits the number of cached entries using an LRU cache.
 * Handles both primitive and object arguments efficiently.
 * @param fn - The function to memoize.
 * @param options - Optional settings for memoization.
 * @returns A memoized version of the function.
 */
export function weakMapMemoize<T extends AnyFunction>(fn: T, options?: WeakMapMemoizeOptions): T {
  const {maxEntries} = options || {};

  // Initialize the root cache node
  const cacheRoot: CacheNode = {
    map: new Map(),
    weakMap: new WeakMap(),
  };

  // Initialize LRU Cache if maxEntries is specified
  let lruCache: LRU<any, any> | null = null;

  if (maxEntries) {
    lruCache = new LRU<any, any>({
      max: maxEntries,
      dispose: (key, _value) => {
        // When an entry is evicted from the LRU cache,
        // traverse the cache tree and remove the cached result
        const keyPath = key as any[];
        let currentCache: CacheNode | undefined = cacheRoot;

        for (let i = 0; i < keyPath.length; i++) {
          const arg = keyPath[i];
          const isArgObject = isObject(arg);

          if (isArgObject) {
            currentCache = currentCache.weakMap.get(arg);
          } else {
            currentCache = currentCache.map.get(arg);
          }

          if (!currentCache) {
            // The cache node has already been removed
            return;
          }
        }

        // Remove the cached result
        delete currentCache.result;
        delete currentCache.lruKey;
      },
    });
  }

  return function memoizedFunction(...args: any[]) {
    let currentCache = cacheRoot;
    const path: any[] = [];

    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      path.push(arg);
      const isArgObject = isObject(arg);

      // Determine the appropriate cache level
      if (isArgObject) {
        if (!currentCache.weakMap.has(arg)) {
          const newCacheNode: CacheNode = {
            map: new Map(),
            weakMap: new WeakMap(),
          };
          currentCache.weakMap.set(arg, newCacheNode);
        }
        currentCache = currentCache.weakMap.get(arg)!;
      } else {
        if (!currentCache.map.has(arg)) {
          const newCacheNode: CacheNode = {
            map: new Map(),
            weakMap: new WeakMap(),
          };
          currentCache.map.set(arg, newCacheNode);
        }
        currentCache = currentCache.map.get(arg)!;
      }
    }

    // After traversing all arguments, check if the result is cached
    if ('result' in currentCache) {
      // If using LRU Cache, update its usage
      if (lruCache && currentCache.lruKey) {
        lruCache.get(currentCache.lruKey); // This updates the recentness
      }
      return currentCache.result;
    }

    // Compute the result
    const result = fn(...args);

    // Cache the result
    currentCache.result = result;

    // If LRU cache is enabled, manage the cache entries
    if (lruCache) {
      const cacheEntryKey: any[] = path.slice(); // Store the whole path so that we can use it in the dispose call to clear the cache
      currentCache.lruKey = cacheEntryKey; // Associate the cache node with the LRU key

      lruCache.set(cacheEntryKey, currentCache);
    }

    return result;
  } as T;
}

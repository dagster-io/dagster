import LRU from 'lru-cache';

type AnyFunction = (...args: any[]) => any;

interface WeakMapMemoizeOptions {
  maxEntries?: number; // Optional limit for cached entries
}

interface CacheNode {
  map: Map<any, CacheNode>;
  weakMap: WeakMap<object, CacheNode>;
  result?: any;
  parent?: CacheNode;
  parentKey?: any;
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
  let lruCache: LRU<any, CacheNode> | null = null;

  if (maxEntries) {
    lruCache = new LRU<any, CacheNode>({
      max: maxEntries,
      dispose: (key, cacheNode) => {
        // When an entry is evicted from the LRU cache, remove it from its parent
        if (cacheNode.parent && cacheNode.parentKey !== undefined) {
          const parent = cacheNode.parent;
          const parentKey = cacheNode.parentKey;

          if (isObject(parentKey)) {
            parent.weakMap.delete(parentKey);
          } else {
            parent.map.delete(parentKey);
          }
        }
      },
      noDisposeOnSet: false, // Ensure dispose is called on eviction
    });
  }

  return function memoizedFunction(...args: any[]) {
    let currentCache = cacheRoot;
    const path: any[] = [];

    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      path.push(arg);
      const isArgObject = isObject(arg);

      let nextCacheNode: CacheNode | undefined;

      if (isArgObject) {
        if (!currentCache.weakMap.has(arg)) {
          const newCacheNode: CacheNode = {
            map: new Map(),
            weakMap: new WeakMap(),
            parent: currentCache,
            parentKey: arg,
          };
          currentCache.weakMap.set(arg, newCacheNode);
        }
        nextCacheNode = currentCache.weakMap.get(arg);
      } else {
        if (!currentCache.map.has(arg)) {
          const newCacheNode: CacheNode = {
            map: new Map(),
            weakMap: new WeakMap(),
            parent: currentCache,
            parentKey: arg,
          };
          currentCache.map.set(arg, newCacheNode);
        }
        nextCacheNode = currentCache.map.get(arg);
      }

      currentCache = nextCacheNode!;
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
      const cacheEntryKey: any[] = path.slice(); // Clone the path to ensure uniqueness
      currentCache.lruKey = cacheEntryKey; // Associate the cache node with the LRU key

      lruCache.set(cacheEntryKey, currentCache);
    }

    return result;
  } as T;
}

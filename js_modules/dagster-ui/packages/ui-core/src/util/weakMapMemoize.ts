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
  childCount: number; // Number of child nodes
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
 * Recursively deletes parent nodes if their childCount reaches zero.
 * @param cacheNode - The cache node to start deletion from.
 */
function recursivelyDeleteParent(cacheNode: CacheNode) {
  if (cacheNode.parent && cacheNode.parentKey !== undefined) {
    const parent = cacheNode.parent;
    const parentKey = cacheNode.parentKey;

    // Remove the current cacheNode from its parent
    if (isObject(parentKey)) {
      parent.weakMap.delete(parentKey);
    } else {
      parent.map.delete(parentKey);
    }

    // Decrement the parent's child count
    parent.childCount--;

    // If the parent's childCount reaches zero and it's not the root, recurse
    if (parent.childCount === 0 && parent.parent) {
      recursivelyDeleteParent(parent);
    }
  }
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
    childCount: 0,
  };

  // Initialize LRU Cache if maxEntries is specified
  let lruCache: LRU<any, CacheNode> | null = null;

  if (maxEntries) {
    lruCache = new LRU<any, CacheNode>({
      max: maxEntries,
      dispose: (_key, cacheNode) => {
        // Remove the cached result
        delete cacheNode.result;

        // If there are no child nodes, proceed to remove this node from its parent
        if (cacheNode.childCount === 0 && cacheNode.parent && cacheNode.parentKey !== undefined) {
          recursivelyDeleteParent(cacheNode);
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
            childCount: 0,
          };
          currentCache.weakMap.set(arg, newCacheNode);
          currentCache.childCount++;
        }
        nextCacheNode = currentCache.weakMap.get(arg);
      } else {
        if (!currentCache.map.has(arg)) {
          const newCacheNode: CacheNode = {
            map: new Map(),
            weakMap: new WeakMap(),
            parent: currentCache,
            parentKey: arg,
            childCount: 0,
          };
          currentCache.map.set(arg, newCacheNode);
          currentCache.childCount++;
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
    if (lruCache && !currentCache.lruKey) {
      const cacheEntryKey = Symbol();
      currentCache.lruKey = cacheEntryKey; // Associate the cache node with the LRU key
      lruCache.set(cacheEntryKey, currentCache);
    }

    return result;
  } as T;
}

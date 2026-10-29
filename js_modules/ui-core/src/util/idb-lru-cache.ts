import debounce from 'lodash/debounce';

import {LRUCache} from './lru-cache';

interface CacheOptions {
  dbName: string;
  dbVersion?: number;
  maxCount: number;
}

class IDBError extends Error {
  constructor(
    message: string,
    public originalError?: unknown,
  ) {
    super(message);
    this.name = 'IDBError';
  }
}

/**
 * A cache that uses IndexedDB to store and retrieve an in-memory LRUCache.
 */
class IDBLRUCache<T> {
  private dbName: string;
  private maxCount: number;
  private dbPromise: Promise<IDBDatabase | null> | undefined;
  private lruCache: LRUCache<T>;
  private dbVersion?: number;
  // Only the first open loads from IndexedDB. A reopen after close() keeps memory, which may hold
  // writes that failed to persist.
  private hasOpened = false;

  constructor({dbName, dbVersion, maxCount}: CacheOptions) {
    this.dbName = `idb-lru-cache-v1-${dbName}`;
    this.maxCount = maxCount;
    this.dbVersion = dbVersion;
    this.lruCache = new LRUCache<T>(maxCount);
    this.getDB();
  }

  private async initDB(): Promise<IDBDatabase> {
    const shouldLoad = !this.hasOpened;
    this.hasOpened = true;
    const request = indexedDB.open(this.dbName, this.dbVersion);

    return new Promise((resolve, reject) => {
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache');
        }
      };
      request.onsuccess = async (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!shouldLoad) {
          resolve(db);
          return;
        }

        try {
          // Load the entire cache from IndexedDB
          const tx = db.transaction('cache', 'readonly');
          const store = tx.objectStore('cache');
          const request = store.get('lru-cache');

          await new Promise<void>((resolve, reject) => {
            request.onsuccess = () => {
              if (request.result) {
                this.lruCache = LRUCache.fromJSON(request.result, this.maxCount);
              }
              resolve();
            };
            request.onerror = () => {
              reject(new IDBError('Failed to load cache', request.error));
            };
          });
        } catch {
          // An unreadable cache starts empty.
        }

        resolve(db);
      };
      request.onerror = (event) => {
        reject(new IDBError('Failed to open database', (event.target as IDBOpenDBRequest).error));
      };
      request.onblocked = () => {
        reject(new IDBError('Database is blocked'));
      };
    });
  }

  /**
   * Resolves to null if IndexedDB is unavailable. Persistence is best-effort, so reads and
   * writes keep working against the in-memory LRU and never reject because of IndexedDB.
   */
  private getDB(): Promise<IDBDatabase | null> {
    if (!this.dbPromise) {
      this.dbPromise = this.initDB().catch(() => null);
    }
    return this.dbPromise;
  }

  private syncToDB = debounce(async (): Promise<void> => {
    const db = await this.getDB();
    if (!db) {
      return;
    }
    try {
      const transaction = db.transaction('cache', 'readwrite');
      const store = transaction.objectStore('cache');

      await new Promise((resolve, reject) => {
        const putRequest = store.put(this.lruCache.toJSON(), 'lru-cache');
        putRequest.onsuccess = () => resolve(void 0);
        putRequest.onerror = () => reject(putRequest.error);
      });
    } catch {
      // e.g. quota exceeded or the browser closed the connection; the in-memory cache is intact.
    }
  }, 1000);

  async set(key: string, value: T): Promise<void> {
    await this.getDB();
    this.lruCache.put(key, value);
    this.syncToDB();
  }

  async get(key: string): Promise<{value: T} | undefined> {
    await this.getDB();
    const value = this.lruCache.get(key);
    return value !== undefined ? {value} : undefined;
  }

  async has(key: string): Promise<boolean> {
    await this.getDB();
    return this.lruCache.get(key) !== undefined;
  }

  async delete(key: string): Promise<void> {
    await this.getDB();
    this.lruCache.put(key, undefined as unknown as T); // Using put to trigger LRU eviction
    this.syncToDB();
  }

  async clear(): Promise<void> {
    await this.getDB();
    this.lruCache = new LRUCache<T>(this.maxCount);
    this.syncToDB();
  }

  async close(): Promise<void> {
    await this.syncToDB.flush();
    const db = await this.getDB();
    delete this.dbPromise;
    db?.close();
  }
}

export function cache<T>(options: CacheOptions): IDBLRUCache<T> {
  return new IDBLRUCache<T>(options);
}

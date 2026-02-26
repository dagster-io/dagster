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
  private dbPromise: Promise<IDBDatabase> | undefined;
  private isDbOpen = false;
  private lruCache: LRUCache<T>;
  private dbVersion?: number;

  constructor({dbName, dbVersion, maxCount}: CacheOptions) {
    this.dbName = `idb-lru-cache-v1-${dbName}`;
    this.maxCount = maxCount;
    this.lruCache = new LRUCache<T>(maxCount);
    this.dbPromise = this.initDB();
    this.dbVersion = dbVersion;
  }

  private async initDB(): Promise<IDBDatabase> {
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
        this.isDbOpen = true;

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

        resolve(db);
      };
      request.onerror = (event) => {
        this.isDbOpen = false;
        reject(new IDBError('Failed to open database', (event.target as IDBOpenDBRequest).error));
      };
      request.onblocked = () => {
        this.isDbOpen = false;
        reject(new IDBError('Database is blocked'));
      };
    });
  }

  private async withDB<T>(operation: (db: IDBDatabase) => Promise<T>): Promise<T> {
    try {
      if (!this.dbPromise) {
        this.dbPromise = this.initDB();
      }
      const db = await this.dbPromise;
      if (!this.isDbOpen) {
        throw new IDBError('Database is not open', this.dbName);
      }
      return await operation(db);
    } catch (error) {
      if (error instanceof IDBError) {
        throw error;
      }
      throw new IDBError('Database operation failed', error);
    }
  }

  private syncToDB = debounce(async (): Promise<void> => {
    return this.withDB(async (db) => {
      const transaction = db.transaction('cache', 'readwrite');
      const store = transaction.objectStore('cache');

      await new Promise((resolve, reject) => {
        const putRequest = store.put(this.lruCache.toJSON(), 'lru-cache');
        putRequest.onsuccess = () => resolve(void 0);
        putRequest.onerror = () => reject(new IDBError('Failed to sync cache', putRequest.error));
      });
    });
  }, 1000);

  async set(key: string, value: T): Promise<void> {
    return this.withDB(async () => {
      this.lruCache.put(key, value);
      this.syncToDB();
    });
  }

  async get(key: string): Promise<{value: T} | undefined> {
    return this.withDB(async () => {
      const value = this.lruCache.get(key);
      return value !== undefined ? {value} : undefined;
    });
  }

  async has(key: string): Promise<boolean> {
    return this.withDB(async () => {
      return this.lruCache.get(key) !== undefined;
    });
  }

  async delete(key: string): Promise<void> {
    return this.withDB(async () => {
      this.lruCache.put(key, undefined as any); // Using put to trigger LRU eviction
      this.syncToDB();
    });
  }

  async clear(): Promise<void> {
    return this.withDB(async () => {
      this.lruCache = new LRUCache<T>(this.maxCount);
      this.syncToDB();
    });
  }

  async close(): Promise<void> {
    await this.syncToDB.flush();
    await this.withDB(async (db) => {
      this.isDbOpen = false;
      delete this.dbPromise;
      db.close();
    });
  }
}

export function cache<T>(options: CacheOptions): IDBLRUCache<T> {
  return new IDBLRUCache<T>(options);
}

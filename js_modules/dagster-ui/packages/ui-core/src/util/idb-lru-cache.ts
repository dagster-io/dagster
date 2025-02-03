interface CacheOptions {
  dbName: string;
  maxCount: number;
  expiry?: Date;
}

interface CacheEntry<T> {
  key: string;
  value: T;
  lastAccessed: number;
  expiry?: number;
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

class IDBLRUCache<T> {
  private dbName: string;
  private maxCount: number;
  private dbPromise: Promise<IDBDatabase>;
  private isDbOpen = false;
  private inMemoryCache = new Map<string, CacheEntry<T>>();
  private cleanupPromise: Promise<void> | undefined;
  private cleanupTimeout: number | undefined;

  constructor({dbName, maxCount}: CacheOptions) {
    this.dbName = dbName;
    this.maxCount = maxCount;
    this.dbPromise = this.initDB();
  }

  private async initDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 2);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('cache')) {
          const store = db.createObjectStore('cache', {keyPath: 'key'});
          store.createIndex('lastAccessed', 'lastAccessed');
        }
      };

      request.onsuccess = async (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        this.isDbOpen = true;

        // Preload in-memory cache with existing entries
        const tx = db.transaction('cache', 'readonly');
        const store = tx.objectStore('cache');
        const request = store.openCursor();

        request.onsuccess = () => {
          const cursor = request.result;
          if (cursor) {
            const entry = cursor.value as CacheEntry<T>;
            this.inMemoryCache.set(entry.key, entry);
            cursor.continue();
          }
        };

        await new Promise((resolve) => (tx.oncomplete = resolve));
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
      const db = await this.dbPromise;
      if (!this.isDbOpen) {
        throw new IDBError('Database is not open');
      }
      return await operation(db);
    } catch (error) {
      if (error instanceof IDBError) {
        throw error;
      }
      throw new IDBError('Database operation failed', error);
    }
  }

  private syncCleanup(): void {
    if (this.inMemoryCache.size <= this.maxCount) {
      return;
    }

    // Sort entries by lastAccessed time
    const sortedEntries = Array.from(this.inMemoryCache.entries()).sort(
      (a, b) => a[1].lastAccessed - b[1].lastAccessed,
    );

    // Determine which keys to remove
    const keysToRemove = sortedEntries
      .slice(0, sortedEntries.length - this.maxCount)
      .map(([key]) => key);

    // Remove from in-memory cache synchronously
    keysToRemove.forEach((key) => this.inMemoryCache.delete(key));

    // Schedule async removal from IndexedDB
    if (keysToRemove.length > 0) {
      this.scheduleCleanup(keysToRemove);
    }
  }

  private scheduleCleanup(keysToRemove?: string[]): void {
    if (this.cleanupTimeout !== undefined) {
      window.clearTimeout(this.cleanupTimeout);
    }

    this.cleanupPromise = new Promise((resolve) => {
      this.cleanupTimeout = window.setTimeout(() => {
        if ('requestIdleCallback' in window) {
          window.requestIdleCallback(async () => {
            if (keysToRemove) {
              await Promise.all(keysToRemove.map((key) => this.deleteFromDB(key)));
            } else {
              await this.cleanup();
            }
            delete this.cleanupPromise;
            resolve(void 0);
          });
        } else {
          // Fallback for browsers without requestIdleCallback
          Promise.resolve().then(async () => {
            if (keysToRemove) {
              await Promise.all(keysToRemove.map((key) => this.deleteFromDB(key)));
            } else {
              await this.cleanup();
            }
            delete this.cleanupPromise;
            resolve(void 0);
          });
        }
      }, 100);
    });
  }

  private async deleteFromDB(key: string): Promise<void> {
    return this.withDB(async (db) => {
      const transaction = db.transaction('cache', 'readwrite');
      const store = transaction.objectStore('cache');

      return new Promise((resolve, reject) => {
        const request = store.delete(key);
        request.onsuccess = () => resolve();
        request.onerror = () => {
          reject(new IDBError('Failed to delete key', request.error));
        };
      });
    });
  }

  async set(key: string, value: T, options?: {expiry?: Date}): Promise<void> {
    const entry: CacheEntry<T> = {
      key,
      value,
      lastAccessed: Date.now(),
      expiry: options?.expiry?.getTime(),
    };

    // Update in-memory cache immediately
    this.inMemoryCache.set(key, entry);
    this.syncCleanup();

    // Schedule IndexedDB update
    return this.withDB(async (db) => {
      const transaction = db.transaction('cache', 'readwrite');
      const store = transaction.objectStore('cache');

      return new Promise((resolve, reject) => {
        const request = store.put(entry);
        request.onsuccess = () => resolve();
        request.onerror = () => {
          reject(new IDBError('Failed to set value', request.error));
        };
      });
    });
  }

  async get(key: string): Promise<{value: T} | undefined> {
    return this.withDB(async (db) => {
      // Check in-memory cache first
      const entry = this.inMemoryCache.get(key);
      if (!entry) {
        return undefined;
      }

      // Check expiry
      if (entry.expiry && Date.now() > entry.expiry) {
        this.delete(key);
        return undefined;
      }

      // Update lastAccessed
      entry.lastAccessed = Date.now();
      this.inMemoryCache.set(key, entry);
      this.syncCleanup();

      const transaction = db.transaction('cache', 'readwrite');
      const store = transaction.objectStore('cache');
      store.put(entry);

      return {value: entry.value};
    });
  }

  async has(key: string): Promise<boolean> {
    return this.withDB(async () => {
      const entry = this.inMemoryCache.get(key);
      if (!entry) {
        return false;
      }
      if (entry.expiry && Date.now() > entry.expiry) {
        this.delete(key);
        return false;
      }
      return true;
    });
  }

  async delete(key: string): Promise<void> {
    return this.withDB(async () => {
      this.inMemoryCache.delete(key);
      this.syncCleanup();
      return this.deleteFromDB(key);
    });
  }

  async clear(): Promise<void> {
    return this.withDB(async (db) => {
      this.inMemoryCache.clear();
      this.syncCleanup();
      const transaction = db.transaction('cache', 'readwrite');
      const store = transaction.objectStore('cache');

      return new Promise((resolve, reject) => {
        const request = store.clear();

        request.onsuccess = () => resolve();
        request.onerror = () => {
          reject(new IDBError('Failed to clear cache', request.error));
        };
      });
    });
  }

  private async cleanup(): Promise<void> {
    this.withDB(async () => {
      // Use only in-memory cache for cleanup decisions
      if (this.inMemoryCache.size <= this.maxCount) {
        return;
      }

      // Sort entries by lastAccessed time
      const sortedEntries = Array.from(this.inMemoryCache.entries()).sort(
        (a, b) => a[1].lastAccessed - b[1].lastAccessed,
      );

      // Determine which keys to remove
      const keysToRemove = sortedEntries
        .slice(0, sortedEntries.length - this.maxCount)
        .map(([key]) => key);

      // Remove from both cache and database
      await Promise.all(keysToRemove.map((key) => this.delete(key)));
    });
  }

  async close(): Promise<void> {
    return this.withDB(async (db) => {
      await new Promise(async (resolve) => {
        if (this.cleanupPromise) {
          await this.cleanupPromise;
        }
        resolve(void 0);
      });
      this.isDbOpen = false;
      db.close();
    });
  }
}

export function cache<T>(options: CacheOptions): IDBLRUCache<T> {
  return new IDBLRUCache<T>(options);
}

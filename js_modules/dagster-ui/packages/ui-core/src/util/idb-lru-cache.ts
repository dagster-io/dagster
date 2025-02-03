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
  private dbPromise: Promise<IDBDatabase> | undefined;
  private isDbOpen = false;
  private inMemoryCache = new Map<string, CacheEntry<T>>();
  private cleanupTimeout: number | undefined;
  private operationQueue: Promise<void> = Promise.resolve();
  private needsSync = false;
  private syncTimeout: number | undefined;

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

  private async withDBInitialized<T>(operation: (db: IDBDatabase) => Promise<T>): Promise<T> {
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

  // This is a helper function to ensure that operations are performed in the order of the operation queue.
  // to avoid race conditions.
  private async withDB<T>(operation: (db: IDBDatabase) => Promise<T>): Promise<T> {
    return this.withDBInitialized(
      (db) =>
        new Promise((resolve, reject) => {
          this.operationQueue = this.operationQueue.then(async () => {
            try {
              const result = await operation(db);
              resolve(result);
            } catch (error) {
              reject(error);
            }
          });
        }),
    );
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

    new Promise((resolve) => {
      this.cleanupTimeout = window.setTimeout(() => {
        if ('requestIdleCallback' in window) {
          window.requestIdleCallback(async () => {
            if (keysToRemove) {
              await Promise.all(keysToRemove.map((key) => this.deleteFromDB(key)));
            } else {
              await this.cleanup();
            }
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
        request.onsuccess = () => {
          resolve();
        };
        request.onerror = () => {
          reject(new IDBError('Failed to delete key', request.error));
        };
      });
    });
  }

  private scheduleSync(): void {
    if (this.syncTimeout !== undefined) {
      return;
    }

    this.syncTimeout = window.setTimeout(() => {
      this.syncToDB().finally(() => {
        this.syncTimeout = undefined;
        if (this.needsSync) {
          this.scheduleSync();
        }
      });
    }, 100); // Debounce time
  }

  private async syncToDB(): Promise<void> {
    if (!this.needsSync) {
      return;
    }

    return this.withDB(async (db) => {
      const transaction = db.transaction('cache', 'readwrite');
      const store = transaction.objectStore('cache');

      // Clear existing entries
      await new Promise((resolve, reject) => {
        const clearRequest = store.clear();
        clearRequest.onsuccess = () => resolve(void 0);
        clearRequest.onerror = () =>
          reject(new IDBError('Failed to clear cache', clearRequest.error));
      });

      // Add all entries from in-memory cache
      const entries = Array.from(this.inMemoryCache.values());
      for (const entry of entries) {
        await new Promise((resolve, reject) => {
          const putRequest = store.put(entry);
          putRequest.onsuccess = () => resolve(void 0);
          putRequest.onerror = () => reject(new IDBError('Failed to set value', putRequest.error));
        });
      }

      this.needsSync = false;
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
    this.needsSync = true;
    this.syncCleanup();
    this.scheduleSync();
  }

  async get(key: string): Promise<{value: T} | undefined> {
    return this.withDBInitialized(async () => {
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

      this.withDB(async (db) => {
        const transaction = db.transaction('cache', 'readwrite');
        const store = transaction.objectStore('cache');
        await store.put(entry);
      });

      return {value: entry.value};
    });
  }

  async has(key: string): Promise<boolean> {
    return this.withDBInitialized(async () => {
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
    this.inMemoryCache.delete(key);
    this.needsSync = true;
    this.syncCleanup();
    this.scheduleSync();
  }

  async clear(): Promise<void> {
    this.inMemoryCache.clear();
    this.needsSync = true;
    this.syncCleanup();
    return this.syncToDB();
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
      this.isDbOpen = false;
      delete this.dbPromise;
      db.close();
    });
  }
}

export function cache<T>(options: CacheOptions): IDBLRUCache<T> {
  return new IDBLRUCache<T>(options);
}

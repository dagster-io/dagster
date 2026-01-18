import {cache} from '../idb-lru-cache';

describe('IDBLRUCache', () => {
  const testCacheOptions = () => ({
    dbName: 'test-cache' + Math.random(),
    maxCount: 3,
  });

  it('should initialize without throwing', async () => {
    const cacheInstance = cache(testCacheOptions());
    expect(cacheInstance).toBeInstanceOf(Object);
    await cacheInstance.close();
  });

  it('should set and get values correctly', async () => {
    const cacheInstance = cache(testCacheOptions());
    await cacheInstance.set('key1', 'value1');
    const result = await cacheInstance.get('key1');
    expect(result?.value).toBe('value1');
    await cacheInstance.close();
  });

  it('should return undefined for non-existent keys', async () => {
    const cacheInstance = cache(testCacheOptions());
    const result = await cacheInstance.get('non-existent');
    expect(result).toBeUndefined();
    await cacheInstance.close();
  });

  it('should enforce maxCount limit', async () => {
    const cacheInstance = cache(testCacheOptions());
    await cacheInstance.set('key1', 'value1');
    await cacheInstance.set('key2', 'value2');
    await cacheInstance.set('key3', 'value3');
    await cacheInstance.set('key4', 'value4');
    const keys = await Promise.all([
      cacheInstance.get('key1'),
      cacheInstance.get('key2'),
      cacheInstance.get('key3'),
      cacheInstance.get('key4'),
    ]);
    // The oldest key (key1) should have been removed
    expect(keys).toEqual([undefined, {value: 'value2'}, {value: 'value3'}, {value: 'value4'}]);
    await cacheInstance.close();
  });

  it('should delete keys correctly', async () => {
    const cacheInstance = cache(testCacheOptions());
    await cacheInstance.set('key1', 'value1');
    await cacheInstance.delete('key1');
    const result = await cacheInstance.get('key1');
    expect(result).toBeUndefined();
    await cacheInstance.close();
  });

  it('should clear the cache', async () => {
    const cacheInstance = cache(testCacheOptions());
    await cacheInstance.set('key1', 'value1');
    await cacheInstance.set('key2', 'value2');
    await cacheInstance.clear();

    const keys = await Promise.all([cacheInstance.has('key1'), cacheInstance.has('key2')]);

    expect(keys).toEqual([false, false]);
    await cacheInstance.close();
  });

  it('should evict least recently used items', async () => {
    const cacheInstance = cache(testCacheOptions());
    await cacheInstance.set('key1', 'value1');
    await cacheInstance.set('key2', 'value2');
    await cacheInstance.set('key3', 'value3');

    // Access key1 to update lastAccessed time
    await cacheInstance.get('key1');

    // Adding a 4th entry should evict the least recently used entry (key2)
    await cacheInstance.set('key4', 'value4');

    const keys = await Promise.all([
      cacheInstance.get('key1'),
      cacheInstance.get('key2'),
      cacheInstance.get('key3'),
      cacheInstance.get('key4'),
    ]);

    // The least recently used key (key2) should have been removed
    expect(keys).toEqual([{value: 'value1'}, undefined, {value: 'value3'}, {value: 'value4'}]);
    await cacheInstance.close();
  });
});

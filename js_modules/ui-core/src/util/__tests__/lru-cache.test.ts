import {LRUCache} from '../lru-cache';

describe('LRUCache', () => {
  let cache: LRUCache<string>;

  beforeEach(() => {
    cache = new LRUCache<string>(3);
  });

  it('should store and retrieve values', () => {
    cache.put('a', '1');
    cache.put('b', '2');
    expect(cache.get('a')).toBe('1');
    expect(cache.get('b')).toBe('2');
  });

  it('should evict least recently used item when capacity is exceeded', () => {
    cache.put('a', '1');
    cache.put('b', '2');
    cache.put('c', '3');
    cache.put('d', '4'); // Should evict 'a'

    expect(cache.get('a')).toBeUndefined();
    expect(cache.get('b')).toBe('2');
    expect(cache.get('c')).toBe('3');
    expect(cache.get('d')).toBe('4');
  });

  it('should update recently used on get', () => {
    cache.put('a', '1');
    cache.put('b', '2');
    cache.put('c', '3');

    // Access 'a' to make it most recently used
    cache.get('a');
    cache.put('d', '4'); // Should evict 'b'

    expect(cache.get('a')).toBe('1');
    expect(cache.get('b')).toBeUndefined();
  });

  it('should update recently used on put', () => {
    cache.put('a', '1');
    cache.put('b', '2');
    cache.put('c', '3');

    // Update 'b' to make it most recently used
    cache.put('b', '2-updated');
    cache.put('d', '4'); // Should evict 'a'

    expect(cache.get('a')).toBeUndefined();
    expect(cache.get('b')).toBe('2-updated');
  });

  it('should handle empty cache', () => {
    expect(cache.get('nonexistent')).toBeUndefined();
  });

  it('should serialize to JSON correctly', () => {
    cache.put('a', '1');
    cache.put('b', '2');
    const serialized = cache.toJSON();

    expect(serialized).toEqual({
      a: '1',
      b: '2',
    });
  });

  it('should deserialize from JSON correctly', () => {
    const data = {
      a: '1',
      b: '2',
      c: '3',
    };
    const deserializedCache = LRUCache.fromJSON(data, 3);

    expect(deserializedCache.get('a')).toBe('1');
    expect(deserializedCache.get('b')).toBe('2');
    expect(deserializedCache.get('c')).toBe('3');
  });

  it('should maintain capacity after deserialization', () => {
    const data = {
      a: '1',
      b: '2',
      c: '3',
      d: '4',
    };
    const deserializedCache = LRUCache.fromJSON(data, 3);

    // Only the last 3 items should be kept
    expect(deserializedCache.get('a')).toBeUndefined();
    expect(deserializedCache.get('b')).toBe('2');
    expect(deserializedCache.get('c')).toBe('3');
    expect(deserializedCache.get('d')).toBe('4');
  });

  it('should handle complex types', () => {
    const objectCache = new LRUCache<{id: number; name: string}>(2);
    objectCache.put('user1', {id: 1, name: 'Alice'});
    objectCache.put('user2', {id: 2, name: 'Bob'});

    expect(objectCache.get('user1')).toEqual({id: 1, name: 'Alice'});
    expect(objectCache.get('user2')).toEqual({id: 2, name: 'Bob'});
  });
});

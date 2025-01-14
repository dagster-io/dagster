import {weakMapMemoize} from '../weakMapMemoize';

type AnyFunction = (...args: any[]) => any;

describe('weakMapMemoize', () => {
  // Test 1: Function with primitive arguments
  it('should memoize correctly with primitive arguments and avoid redundant calls', () => {
    const spy = jest.fn((a: number, b: number) => a + b);
    const memoizedAdd = weakMapMemoize(spy, {maxEntries: 3});

    expect(memoizedAdd(1, 2)).toBe(3);
    expect(memoizedAdd(1, 2)).toBe(3);
    expect(memoizedAdd(2, 3)).toBe(5);
    expect(spy).toHaveBeenCalledTimes(2); // Only two unique calls
  });

  // Test 2: Function with object arguments
  it('should memoize correctly based on object references', () => {
    const spy = jest.fn((obj: {x: number}, y: number) => obj.x + y);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 2});

    const obj1 = {x: 10};
    const obj2 = {x: 20};

    expect(memoizedFn(obj1, 5)).toBe(15);
    expect(memoizedFn(obj1, 5)).toBe(15);
    expect(memoizedFn(obj2, 5)).toBe(25);
    expect(memoizedFn(obj1, 6)).toBe(16);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 3: Function with mixed arguments
  it('should memoize correctly with mixed primitive and object arguments', () => {
    const spy = jest.fn((a: number, obj: {y: number}) => a + obj.y);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    const obj1 = {y: 100};
    const obj2 = {y: 200};

    expect(memoizedFn(1, obj1)).toBe(101);
    expect(memoizedFn(1, obj1)).toBe(101);
    expect(memoizedFn(2, obj1)).toBe(102);
    expect(memoizedFn(1, obj2)).toBe(201);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 4: Function with no arguments
  it('should memoize the result when function has no arguments', () => {
    const spy = jest.fn(() => Math.random());
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 1});

    const result1 = memoizedFn();
    const result2 = memoizedFn();
    const result3 = memoizedFn();

    expect(result1).toBe(result2);
    expect(result2).toBe(result3);
    expect(spy).toHaveBeenCalledTimes(1); // Only one unique call
  });

  // Test 5: Function with null and undefined arguments
  it('should handle null and undefined arguments correctly', () => {
    const spy = jest.fn((a: any, b: any) => {
      if (a === null && b === undefined) {
        return 'null-undefined';
      }
      return 'other';
    });
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 2});

    expect(memoizedFn(null, undefined)).toBe('null-undefined');
    expect(memoizedFn(null, undefined)).toBe('null-undefined');
    expect(memoizedFn(undefined, null)).toBe('other');
    expect(memoizedFn(null, undefined)).toBe('null-undefined');
    expect(spy).toHaveBeenCalledTimes(2); // Two unique calls
  });

  // Test 6: Function with function arguments
  it('should memoize based on function references', () => {
    const spy = jest.fn((fn: AnyFunction, value: number) => fn(value));
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    const func1 = (x: number) => x * 2;
    const func2 = (x: number) => x * 3;

    expect(memoizedFn(func1, 5)).toBe(10);
    expect(memoizedFn(func1, 5)).toBe(10);
    expect(memoizedFn(func2, 5)).toBe(15);
    expect(memoizedFn(func1, 6)).toBe(12);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 7: Function with multiple mixed arguments
  it('should memoize correctly with multiple mixed argument types', () => {
    const spy = jest.fn((a: number, b: string, c: {key: string}) => `${a}-${b}-${c.key}`);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 4});

    const obj1 = {key: 'value1'};
    const obj2 = {key: 'value2'};

    expect(memoizedFn(1, 'test', obj1)).toBe('1-test-value1');
    expect(memoizedFn(1, 'test', obj1)).toBe('1-test-value1');
    expect(memoizedFn(1, 'test', obj2)).toBe('1-test-value2');
    expect(memoizedFn(2, 'test', obj1)).toBe('2-test-value1');
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 8: Function with array arguments
  it('should memoize based on array references', () => {
    const spy = jest.fn((arr: number[]) => arr.reduce((sum, val) => sum + val, 0));
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    const array1 = [1, 2, 3];
    const array2 = [4, 5, 6];

    expect(memoizedFn(array1)).toBe(6);
    expect(memoizedFn(array1)).toBe(6);
    expect(memoizedFn(array2)).toBe(15);
    expect(memoizedFn([1, 2, 3])).toBe(6);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 9: Function with symbols as arguments
  it('should memoize based on symbol references', () => {
    const sym1 = Symbol('sym1');
    const sym2 = Symbol('sym2');

    const spy = jest.fn((a: symbol, b: number) => a.toString() + b);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 4});

    expect(memoizedFn(sym1, 10)).toBe(`${sym1.toString()}10`);
    expect(memoizedFn(sym1, 10)).toBe(`${sym1.toString()}10`);
    expect(memoizedFn(sym2, 10)).toBe(`${sym2.toString()}10`);
    expect(memoizedFn(sym1, 20)).toBe(`${sym1.toString()}20`);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 10: Function with a large number of arguments
  it('should memoize correctly with a large number of arguments', () => {
    const spy = jest.fn((...args: number[]) => args.reduce((sum, val) => sum + val, 0));
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 5});

    const args1 = [1, 2, 3, 4, 5];
    const args2 = [1, 2, 3, 4, 5];
    const args3 = [5, 4, 3, 2, 1];
    const args4 = [1, 2, 3, 4, 6];
    const args5 = [6, 5, 4, 3, 2];
    const args6 = [1, 2, 3, 4, 7];

    expect(memoizedFn(...args2)).toBe(15);
    expect(memoizedFn(...args1)).toBe(15);
    expect(memoizedFn(...args3)).toBe(15);
    expect(memoizedFn(...args4)).toBe(16);
    expect(memoizedFn(...args5)).toBe(20);
    expect(memoizedFn(...args6)).toBe(17);
    expect(spy).toHaveBeenCalledTimes(5); // Five unique calls (args1, args3, args4, args5, args6)
  });

  // Test 11: Function with alternating object and primitive arguments
  it('should memoize correctly with alternating object and primitive arguments', () => {
    const spy = jest.fn(
      (
        obj1: {a: number},
        prim1: string,
        obj2: {b: number},
        prim2: boolean,
        obj3: {c: number},
        prim3: number,
      ) => obj1.a + prim1.length + obj2.b + (prim2 ? 1 : 0) + obj3.c + prim3,
    );
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 7});

    const object1 = {a: 5};
    const object2 = {b: 10};
    const object3 = {c: 15};
    const object4 = {a: 30};
    const object5 = {b: 20};
    const object6 = {c: 25};

    expect(memoizedFn(object1, 'test', object2, true, object3, 20)).toBe(5 + 4 + 10 + 1 + 15 + 20); // 55
    expect(memoizedFn(object4, 'test', object2, true, object3, 20)).toBe(30 + 4 + 10 + 1 + 15 + 20); // 80
    expect(memoizedFn(object1, 'testing', object2, true, object3, 20)).toBe(
      5 + 7 + 10 + 1 + 15 + 20,
    ); // 58
    expect(memoizedFn(object1, 'test', object5, true, object3, 20)).toBe(5 + 4 + 20 + 1 + 15 + 20); // 65
    expect(memoizedFn(object1, 'test', object2, false, object3, 20)).toBe(5 + 4 + 10 + 0 + 15 + 20); // 54
    expect(memoizedFn(object1, 'test', object2, true, object6, 20)).toBe(5 + 4 + 10 + 1 + 25 + 20); // 65
    expect(memoizedFn(object1, 'test', object2, true, object3, 30)).toBe(5 + 4 + 10 + 1 + 15 + 30); // 65
    expect(memoizedFn(object1, 'testing', object2, false, object3, 30)).toBe(
      5 + 7 + 10 + 0 + 15 + 30,
    ); // 67
    expect(memoizedFn(object1, 'test', object2, true, object3, 20)).toBe(55); // Cached

    // spy should be called for each unique combination
    expect(spy).toHaveBeenCalledTimes(9);
  });

  // Test 12: Exercising the maxEntries option
  it('should evict least recently used entries when maxEntries is exceeded', () => {
    const spy = jest.fn((a: number) => a * 2);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 2});

    expect(memoizedFn(1)).toBe(2);
    expect(memoizedFn(2)).toBe(4);
    expect(memoizedFn(3)).toBe(6); // Evicts least recently used (1)
    expect(memoizedFn(2)).toBe(4); // Cached, updates recentness
    expect(memoizedFn(4)).toBe(8); // Evicts least recently used (3)
    expect(spy).toHaveBeenCalledTimes(4); // Calls for 1,2,3,4

    // Accessing 1 again should trigger a new call since it was evicted
    expect(memoizedFn(1)).toBe(2); // Cached
    expect(spy).toHaveBeenCalledTimes(5); // Call for 1 again
  });

  // Test 13: Should handle mixed argument types in same slot
  it('Should handle mixed argument types in same slot', () => {
    const spy = jest.fn((a: any, b: any) => {
      const toString = (arg: any) => (typeof arg === 'object' ? Object.keys(arg).length : arg);
      return toString(a) + toString(b);
    });
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    expect(memoizedFn(1, 2)).toBe(3);

    expect(memoizedFn(1, 2)).toBe(3);
    expect(spy).toHaveBeenCalledTimes(1);

    expect(memoizedFn('hello', {x: 1, y: 2})).toBe('hello2');
    expect(spy).toHaveBeenCalledTimes(2);

    // Different object reference results in another call
    expect(memoizedFn('hello', {x: 1, y: 2})).toBe('hello2');
    expect(spy).toHaveBeenCalledTimes(3);

    const a = {a: 1};
    expect(memoizedFn(a, 'test')).toBe('1test');
    expect(spy).toHaveBeenCalledTimes(4);

    // same reference uses cache
    expect(memoizedFn(a, 'test')).toBe('1test');
    expect(spy).toHaveBeenCalledTimes(4);

    // Evicts 1, 2
    expect(memoizedFn(3, 4)).toBe(7);
    expect(spy).toHaveBeenCalledTimes(5);

    // Evicted - results in new call
    expect(memoizedFn(1, 2)).toBe(3);
    expect(spy).toHaveBeenCalledTimes(6);
  });

  // Test 14: Evicting a cache node without children deletes its result
  it('should delete the result of an evicted cache node without children', () => {
    const spy = jest.fn((a: number, b: number) => a + b);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 2});

    expect(memoizedFn(1, 1)).toBe(2);
    expect(memoizedFn(2, 2)).toBe(4);
    expect(spy).toHaveBeenCalledTimes(2); // Two unique calls

    // This should evict the least recently used entry (1,1)
    expect(memoizedFn(3, 3)).toBe(6);
    expect(spy).toHaveBeenCalledTimes(3); // New call for (3,3)

    // Accessing (1,1) again should trigger a new function call since it was evicted, and evict (2, 2)
    expect(memoizedFn(1, 1)).toBe(2);
    expect(spy).toHaveBeenCalledTimes(4); // New call for (1,1)

    // evicts 3,3
    expect(memoizedFn(2, 2)).toBe(4);
    expect(spy).toHaveBeenCalledTimes(5);

    expect(memoizedFn(3, 3)).toBe(6);
    expect(spy).toHaveBeenCalledTimes(6);
  });

  // Test 15: Evicting a cache node with children deletes only its result, children remain cached
  it('should delete only the result of an evicted cache node with children and keep children cached', () => {
    const spy = jest.fn((a: number, b: string, c?: number) => a + b.length + (c ?? 0));
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    // Creating cache nodes:
    // (1, 'a')
    // (1, 'a', 10)
    // (2, 'b', 30)

    expect(memoizedFn(1, 'a')).toBe(1 + 1);
    expect(memoizedFn(1, 'a', 10)).toBe(1 + 1 + 10);
    expect(memoizedFn(2, 'b', 30)).toBe(2 + 1 + 30);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls

    // At this point, maxEntries is 3:
    // Cache contains:
    // (1, 'a'), (1, 'a', 10), (2, 'b', 30)

    // Adding a new entry should evict the least recently used, which is (1, 'a')
    expect(memoizedFn(1, 'c', 40)).toBe(1 + 1 + 40);
    expect(spy).toHaveBeenCalledTimes(4);

    // Now, cache contains:
    // (1, 'a', 10), (2, 'b', 30), (1, 'c', 40)
    expect(memoizedFn(1, 'a', 10)).toBe(1 + 1 + 10);
    expect(spy).toHaveBeenCalledTimes(4); // no new call

    // Now, cache contains:
    // (2, 'b', 30), (1, 'c', 40), (1, 'a', 10)
    // Evicting (2, 'b', 30)
    expect(memoizedFn(4, 'd', 50)).toBe(4 + 1 + 50);
    expect(spy).toHaveBeenCalledTimes(5);

    // Now, cache contains:
    // (1, 'c', 40), (1, 'a', 10), (4, 'd', 50)

    // Accessing (1, 'a', 10) again should trigger a new call since it was evicted and evict (2, b, 30)
    expect(memoizedFn(2, 'b', 30)).toBe(2 + 1 + 30);
    expect(spy).toHaveBeenCalledTimes(6);

    // Now, cache contains:
    // (1, 'a', 10), (4, 'd', 50), (2, 'b', 30)

    expect(memoizedFn(1, 'a', 10)).toBe(12);
    expect(memoizedFn(4, 'd', 50)).toBe(55);
    expect(memoizedFn(2, 'b', 30)).toBe(33);

    expect(spy).toHaveBeenCalledTimes(6);
  });
});

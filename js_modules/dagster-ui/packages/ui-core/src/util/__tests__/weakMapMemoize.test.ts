import {weakMapMemoize} from '../weakMapMemoize';

type AnyFunction = (...args: any[]) => any;

describe('weakMapMemoize', () => {
  // Test 1: Function with primitive arguments
  it('should memoize correctly with primitive arguments and avoid redundant calls', () => {
    const spy = jest.fn((a: number, b: number) => a + b);
    const memoizedAdd = weakMapMemoize(spy, {maxEntries: 3});

    const result1 = memoizedAdd(1, 2);
    const result2 = memoizedAdd(1, 2);
    const result3 = memoizedAdd(2, 3);

    expect(result1).toBe(3);
    expect(result2).toBe(3);
    expect(result3).toBe(5);
    expect(spy).toHaveBeenCalledTimes(2); // Only two unique calls
  });

  // Test 2: Function with object arguments
  it('should memoize correctly based on object references', () => {
    const spy = jest.fn((obj: {x: number}, y: number) => obj.x + y);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 2});

    const obj1 = {x: 10};
    const obj2 = {x: 20};

    const result1 = memoizedFn(obj1, 5);
    const result2 = memoizedFn(obj1, 5);
    const result3 = memoizedFn(obj2, 5);
    const result4 = memoizedFn(obj1, 6);

    expect(result1).toBe(15);
    expect(result2).toBe(15);
    expect(result3).toBe(25);
    expect(result4).toBe(16);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 3: Function with mixed arguments
  it('should memoize correctly with mixed primitive and object arguments', () => {
    const spy = jest.fn((a: number, obj: {y: number}) => a + obj.y);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    const obj1 = {y: 100};
    const obj2 = {y: 200};

    const result1 = memoizedFn(1, obj1);
    const result2 = memoizedFn(1, obj1);
    const result3 = memoizedFn(2, obj1);
    const result4 = memoizedFn(1, obj2);

    expect(result1).toBe(101);
    expect(result2).toBe(101);
    expect(result3).toBe(102);
    expect(result4).toBe(201);
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

    const result1 = memoizedFn(null, undefined);
    const result2 = memoizedFn(null, undefined);
    const result3 = memoizedFn(undefined, null);
    const result4 = memoizedFn(null, undefined);

    expect(result1).toBe('null-undefined');
    expect(result2).toBe('null-undefined');
    expect(result3).toBe('other');
    expect(result4).toBe('null-undefined');
    expect(spy).toHaveBeenCalledTimes(2); // Two unique calls
  });

  // Test 6: Function with function arguments
  it('should memoize based on function references', () => {
    const spy = jest.fn((fn: AnyFunction, value: number) => fn(value));
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    const func1 = (x: number) => x * 2;
    const func2 = (x: number) => x * 3;

    const result1 = memoizedFn(func1, 5);
    const result2 = memoizedFn(func1, 5);
    const result3 = memoizedFn(func2, 5);
    const result4 = memoizedFn(func1, 6);

    expect(result1).toBe(10);
    expect(result2).toBe(10);
    expect(result3).toBe(15);
    expect(result4).toBe(12);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 7: Function with multiple mixed arguments
  it('should memoize correctly with multiple mixed argument types', () => {
    const spy = jest.fn((a: number, b: string, c: {key: string}) => `${a}-${b}-${c.key}`);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 4});

    const obj1 = {key: 'value1'};
    const obj2 = {key: 'value2'};

    const result1 = memoizedFn(1, 'test', obj1);
    const result2 = memoizedFn(1, 'test', obj1);
    const result3 = memoizedFn(1, 'test', obj2);
    const result4 = memoizedFn(2, 'test', obj1);

    expect(result1).toBe('1-test-value1');
    expect(result2).toBe('1-test-value1');
    expect(result3).toBe('1-test-value2');
    expect(result4).toBe('2-test-value1');
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 8: Function with array arguments
  it('should memoize based on array references', () => {
    const spy = jest.fn((arr: number[]) => arr.reduce((sum, val) => sum + val, 0));
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 3});

    const array1 = [1, 2, 3];
    const array2 = [4, 5, 6];

    const result1 = memoizedFn(array1);
    const result2 = memoizedFn(array1);
    const result3 = memoizedFn(array2);
    const result4 = memoizedFn([1, 2, 3]); // Different reference

    expect(result1).toBe(6);
    expect(result2).toBe(6);
    expect(result3).toBe(15);
    expect(result4).toBe(6);
    expect(spy).toHaveBeenCalledTimes(3); // Three unique calls
  });

  // Test 9: Function with symbols as arguments
  it('should memoize based on symbol references', () => {
    const sym1 = Symbol('sym1');
    const sym2 = Symbol('sym2');

    const spy = jest.fn((a: symbol, b: number) => a.toString() + b);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 4});

    const result1 = memoizedFn(sym1, 10);
    const result2 = memoizedFn(sym1, 10);
    const result3 = memoizedFn(sym2, 10);
    const result4 = memoizedFn(sym1, 20);

    expect(result1).toBe(`${sym1.toString()}10`);
    expect(result2).toBe(`${sym1.toString()}10`);
    expect(result3).toBe(`${sym2.toString()}10`);
    expect(result4).toBe(`${sym1.toString()}20`);
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

    const result1 = memoizedFn(...args1);
    const result2 = memoizedFn(...args2);
    const result3 = memoizedFn(...args3);
    const result4 = memoizedFn(...args4);
    const result5 = memoizedFn(...args5);
    const result6 = memoizedFn(...args6);

    expect(result1).toBe(15);
    expect(result2).toBe(15);
    expect(result3).toBe(15);
    expect(result4).toBe(16);
    expect(result5).toBe(20);
    expect(result6).toBe(17);
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
    const object5 = {b: 20}; // Corrected to have 'b' property
    const object6 = {c: 25}; // Corrected to have 'c' property

    // First unique call
    const result1 = memoizedFn(object1, 'test', object2, true, object3, 20); // 5 +4 +10 +1 +15 +20 =55

    // Different object in first argument
    const result2 = memoizedFn(object4, 'test', object2, true, object3, 20); // 30 +4 +10 +1 +15 +20 =55

    // Different primitive in second argument
    const result3 = memoizedFn(object1, 'testing', object2, true, object3, 20); //5 +7 +10 +1 +15 +20=58

    // Different object in third argument
    const result4 = memoizedFn(object1, 'test', object5, true, object3, 20); //5 +4 +20 +1 +15 +20=65

    // Different primitive in fourth argument
    const result5 = memoizedFn(object1, 'test', object2, false, object3, 20); //5 +4 +10 +0 +15 +20=54

    // Different object in fifth argument
    const result6 = memoizedFn(object1, 'test', object2, true, object6, 20); //5 +4 +10 +1 +25 +20=65

    // Different primitive in sixth argument
    const result7 = memoizedFn(object1, 'test', object2, true, object3, 30); //5 +4 +10 +1 +15 +30=65

    // Different objects and primitives
    const result8 = memoizedFn(object1, 'testing', object2, false, object3, 30); //5 +7 +10 +0 +15 +30=67

    // Duplicate of the first call again
    const result9 = memoizedFn(object1, 'test', object2, true, object3, 20);
    expect(result1).toBe(5 + 4 + 10 + 1 + 15 + 20); // 55
    expect(result2).toBe(30 + 4 + 10 + 1 + 15 + 20); // Cached
    expect(result3).toBe(5 + 7 + 10 + 1 + 15 + 20); // 58
    expect(result4).toBe(5 + 4 + 20 + 1 + 15 + 20); // 65
    expect(result5).toBe(5 + 4 + 10 + 0 + 15 + 20); // 54
    expect(result6).toBe(5 + 4 + 10 + 1 + 25 + 20); // 65
    expect(result7).toBe(5 + 4 + 10 + 1 + 15 + 30); // 65
    expect(result8).toBe(5 + 7 + 10 + 0 + 15 + 30); // 67
    expect(result9).toBe(55); // Cached

    // spy should be called for each unique combination
    // Unique calls: result1, result3, result4, result5, result6, result7, result8
    // Total unique calls: 7
    expect(spy).toHaveBeenCalledTimes(9);
  });

  // Test 12: Exercising the maxEntries option
  it('should evict least recently used entries when maxEntries is exceeded', () => {
    const spy = jest.fn((a: number) => a * 2);
    const memoizedFn = weakMapMemoize(spy, {maxEntries: 2});

    const result1 = memoizedFn(1); // Cached
    const result2 = memoizedFn(2); // Cached
    const result3 = memoizedFn(3); // Evicts least recently used (1)
    const result4 = memoizedFn(2); // Cached, updates recentness
    const result5 = memoizedFn(4); // Evicts least recently used (3)

    expect(result1).toBe(2);
    expect(result2).toBe(4);
    expect(result3).toBe(6);
    expect(result4).toBe(4);
    expect(result5).toBe(8);
    expect(spy).toHaveBeenCalledTimes(4); // Calls for 1,2,3,4

    // Accessing 1 again should trigger a new call since it was evicted
    const result6 = memoizedFn(1);
    expect(result6).toBe(2);
    expect(spy).toHaveBeenCalledTimes(5); // Call for 1 again
  });
});

import {generateObjectHashStream} from '../generateObjectHash';

describe('generateObjectHashStream', () => {
  test('hashes a simple object correctly', async () => {
    const obj1 = {b: 2, a: 1};
    const obj2 = {a: 1, b: 2};

    const hash1 = await generateObjectHashStream(obj1);
    const hash2 = await generateObjectHashStream(obj2);

    expect(hash1).toBe(hash2); // Should be equal since keys are sorted
  });

  test('hashes nested objects and arrays correctly', async () => {
    const obj1 = {
      user: {
        id: 1,
        name: 'Alice',
        roles: ['admin', 'user'],
      },
      active: true,
    };

    const obj2 = {
      active: true,
      user: {
        roles: ['admin', 'user'],
        name: 'Alice',
        id: 1,
      },
    };

    const hash1 = await generateObjectHashStream(obj1);
    const hash2 = await generateObjectHashStream(obj2);

    expect(hash1).toBe(hash2); // Should be equal due to sorted keys
  });

  test('differentiates between different objects', async () => {
    const obj1 = {a: [1]};
    const obj2 = {a: [2]};
    const hash1 = await generateObjectHashStream(obj1);
    const hash2 = await generateObjectHashStream(obj2);
    expect(hash1).not.toBe(hash2); // Should be different
  });

  test('handles arrays correctly', async () => {
    const arr1 = [1, 2, 3];
    const arr2 = [1, 2, 3];
    const arr3 = [3, 2, 1];

    const hash1 = await generateObjectHashStream(arr1);
    const hash2 = await generateObjectHashStream(arr2);
    const hash3 = await generateObjectHashStream(arr3);

    expect(hash1).toBe(hash2);
    expect(hash1).not.toBe(hash3);
  });

  test('handles empty objects and arrays', async () => {
    const emptyObj = {};
    const emptyArr: any[] = [];

    const hashObj = await generateObjectHashStream(emptyObj);
    const hashArr = await generateObjectHashStream(emptyArr);

    expect(hashObj).not.toEqual(hashArr);
  });

  test('handles nested arrays correctly', async () => {
    const obj1 = {
      a: [
        [1, 2],
        [3, 4],
      ],
    };
    const obj2 = {
      a: [
        [1, 2],
        [3, 5],
      ],
    };

    const hash1 = await generateObjectHashStream(obj1);
    const hash2 = await generateObjectHashStream(obj2);

    expect(hash1).not.toBe(hash2);
  });

  test('handles different property types', async () => {
    const obj1 = {a: 1, b: 'text', c: true};
    const obj2 = {a: 1, b: 'text', c: false};

    const hash1 = await generateObjectHashStream(obj1);
    const hash2 = await generateObjectHashStream(obj2);

    expect(hash1).not.toBe(hash2);
  });
});

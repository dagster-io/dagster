import SparkMD5 from 'spark-md5';

/**
 * Generates a hash for a JSON-serializable object using incremental JSON serialization
 * and SparkMD5 for hashing.
 *
 * @param obj - The JSON-serializable object to hash.
 * @param replacer - Optional JSON.stringify replacer function.
 * @returns The hexadecimal string representation of the hash.
 */
export function generateObjectHashStream(
  obj: Record<string, unknown> | unknown[],
  replacer?: (key: string, value: unknown) => unknown,
): string {
  const hash = new SparkMD5.ArrayBuffer();
  const encoder = new TextEncoder();

  type Frame = {
    obj: Record<string, unknown> | unknown[];
    keys: (string | number)[];
    index: number;
    isArray: boolean;
    isFirst: boolean;
  };

  const stack: Frame[] = [];
  const isRootArray = Array.isArray(obj);
  const initialKeys = isRootArray ? Array.from(Array(obj.length).keys()) : Object.keys(obj).sort();
  stack.push({
    obj,
    keys: initialKeys,
    index: 0,
    isArray: isRootArray,
    isFirst: true,
  });

  hash.append(encoder.encode(isRootArray ? '[' : '{') as unknown as ArrayBuffer);

  while (stack.length > 0) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const currentFrame = stack[stack.length - 1]!;

    if (currentFrame.index >= currentFrame.keys.length) {
      stack.pop();
      hash.append(encoder.encode(currentFrame.isArray ? ']' : '}') as unknown as ArrayBuffer);
      if (stack.length > 0) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const parentFrame = stack[stack.length - 1]!;
        parentFrame.isFirst = false;
      }
      continue;
    }

    if (!currentFrame.isFirst) {
      hash.append(encoder.encode(',') as unknown as ArrayBuffer);
    }
    currentFrame.isFirst = false;

    const key = currentFrame.keys[currentFrame.index];
    currentFrame.index += 1;

    let value: unknown;
    if (currentFrame.isArray) {
      value = (currentFrame.obj as unknown[])[key as number];
    } else {
      value = (currentFrame.obj as Record<string, unknown>)[key as string];
    }

    value = replacer ? replacer(currentFrame.isArray ? '' : String(key), value) : value;

    if (!currentFrame.isArray) {
      const serializedKey = JSON.stringify(key) + ':';
      hash.append(encoder.encode(serializedKey) as unknown as ArrayBuffer);
    }

    if (value && typeof value === 'object') {
      const objValue = value as Record<string, unknown> | unknown[];
      if (Array.isArray(objValue)) {
        hash.append(encoder.encode('[') as unknown as ArrayBuffer);
        const childKeys = Array.from(Array(objValue.length).keys());
        stack.push({
          obj: objValue,
          keys: childKeys,
          index: 0,
          isArray: true,
          isFirst: true,
        });
      } else {
        const childKeys = Object.keys(objValue).sort();
        hash.append(encoder.encode('{') as unknown as ArrayBuffer);
        stack.push({
          obj: objValue,
          keys: childKeys,
          index: 0,
          isArray: false,
          isFirst: true,
        });
      }
    } else {
      const serializedValue = JSON.stringify(value);
      hash.append(encoder.encode(serializedValue) as unknown as ArrayBuffer);
    }
  }

  return hash.end();
}

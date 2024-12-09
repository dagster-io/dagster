import SparkMD5 from 'spark-md5';

/**
 * Generates a hash for a JSON-serializable object using incremental JSON serialization
 * and SparkMD5 for hashing.
 *
 * @param obj - The JSON-serializable object to hash.
 * @param replacer - Optional JSON.stringify replacer function.
 * @returns A Promise that resolves to the hexadecimal string representation of the hash.
 */
export function generateObjectHashStream(
  obj: any,
  replacer?: (key: string, value: any) => any,
): string {
  const hash = new SparkMD5.ArrayBuffer();
  const encoder = new TextEncoder();

  type Frame = {
    obj: any;
    keys: string[] | number[];
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

  hash.append(encoder.encode(isRootArray ? '[' : '{'));

  while (stack.length > 0) {
    const currentFrame = stack[stack.length - 1]!;

    if (currentFrame.index >= currentFrame.keys.length) {
      stack.pop();
      hash.append(encoder.encode(currentFrame.isArray ? ']' : '}'));
      if (stack.length > 0) {
        const parentFrame = stack[stack.length - 1]!;
        parentFrame.isFirst = false;
      }
      continue;
    }

    if (!currentFrame.isFirst) {
      hash.append(encoder.encode(','));
    }
    currentFrame.isFirst = false;

    const key = currentFrame.keys[currentFrame.index];
    currentFrame.index += 1;

    let value: any;
    if (currentFrame.isArray) {
      value = currentFrame.obj[key as number];
    } else {
      value = currentFrame.obj[key as string];
    }

    value = replacer ? replacer(currentFrame.isArray ? '' : String(key), value) : value;

    if (!currentFrame.isArray) {
      const serializedKey = JSON.stringify(key) + ':';
      hash.append(encoder.encode(serializedKey));
    }

    if (value && typeof value === 'object') {
      if (Array.isArray(value)) {
        hash.append(encoder.encode('['));
        const childKeys = Array.from(Array(value.length).keys());
        stack.push({
          obj: value,
          keys: childKeys,
          index: 0,
          isArray: true,
          isFirst: true,
        });
      } else {
        const childKeys = Object.keys(value).sort();
        hash.append(encoder.encode('{'));
        stack.push({
          obj: value,
          keys: childKeys,
          index: 0,
          isArray: false,
          isFirst: true,
        });
      }
    } else {
      const serializedValue = JSON.stringify(value);
      hash.append(encoder.encode(serializedValue));
    }
  }

  return hash.end();
}

/**
 * Creates a fast deterministic hash from a large JSON object iteratively
 * @param obj - The JSON object to hash (must not contain circular references)
 * @returns A deterministic hash string
 */
export function hashObject(obj: any): string {
  // Using MurmurHash3
  let h1: number = 0x12345678; // Seed

  // Constants for MurmurHash3
  const c1: number = 0xcc9e2d51;
  const c2: number = 0x1b873593;

  // Faster hash update function (based on MurmurHash3)
  function hashChunk(str: string): void {
    let k1: number;

    // Process string in 4-byte chunks for speed
    for (let i = 0; i < str.length; i += 4) {
      // Pack up to 4 bytes into a 32-bit int
      k1 = 0;
      const remaining = Math.min(4, str.length - i);
      for (let j = 0; j < remaining; j++) {
        k1 |= str.charCodeAt(i + j) << (j * 8);
      }

      // MurmurHash3 algorithm
      k1 *= c1;
      k1 = (k1 << 15) | (k1 >>> 17);
      k1 *= c2;

      h1 ^= k1;
      h1 = (h1 << 13) | (h1 >>> 19);
      h1 = h1 * 5 + 0xe6546b64;
    }
  }

  // Use a more efficient stack representation with fewer objects
  // Each object creation is expensive, so we'll reuse objects where possible
  const TYPE_PRIMITIVE = 0;
  const TYPE_ARRAY = 1;
  const TYPE_OBJECT = 2;

  interface StackItem {
    type: number; // 0=primitive, 1=array, 2=object
    value: any; // The actual value
    keys?: string[]; // Sorted keys for objects
    index: number; // Current index in array/keys
    state: number; // 0=start, 1=processing, 2=done
  }

  // Initial stack with just the root object
  const stack: StackItem[] = [
    {
      type:
        typeof obj === 'object' && obj !== null
          ? Array.isArray(obj)
            ? TYPE_ARRAY
            : TYPE_OBJECT
          : TYPE_PRIMITIVE,
      value: obj,
      index: 0,
      state: 0,
    },
  ];

  // Small string buffer to avoid creating too many strings
  const smallBuffer = ['{', '}', '[', ']', ':', ',', 'null', 'true', 'false'] as const;

  // Process the object iteratively
  while (stack.length > 0) {
    const current = stack[stack.length - 1]!;

    // Start processing a new item
    if (current.state === 0) {
      current.state = 1;

      // Process based on type
      if (current.type === TYPE_PRIMITIVE) {
        if (current.value === null) {
          hashChunk(smallBuffer[6]); // 'null'
        } else if (typeof current.value === 'boolean') {
          hashChunk(current.value ? smallBuffer[7] : smallBuffer[8]); // 'true' or 'false'
        } else if (typeof current.value === 'number') {
          // Use a consistent string representation for numbers
          hashChunk(current.value.toString());
        } else if (typeof current.value === 'string') {
          hashChunk(current.value);
        }
        current.state = 2; // Mark as done
      } else if (current.type === TYPE_ARRAY) {
        hashChunk(smallBuffer[2]); // '['

        if (current.value.length === 0) {
          hashChunk(smallBuffer[3]); // ']'
          current.state = 2; // Mark as done
        }
      } else if (current.type === TYPE_OBJECT) {
        hashChunk(smallBuffer[0]); // '{'

        // Sort keys once and cache them
        current.keys = Object.keys(current.value).sort();

        if (current.keys.length === 0) {
          hashChunk(smallBuffer[1]); // '}'
          current.state = 2; // Mark as done
        }
      }
    }
    // Process array/object elements
    else if (current.state === 1) {
      if (current.type === TYPE_ARRAY) {
        const arr = current.value;

        if (current.index > 0) {
          hashChunk(smallBuffer[5]); // ','
        }

        if (current.index < arr.length) {
          const item = arr[current.index++];
          const itemType =
            item === null || typeof item !== 'object'
              ? TYPE_PRIMITIVE
              : Array.isArray(item)
                ? TYPE_ARRAY
                : TYPE_OBJECT;

          // Push the item onto the stack
          stack.push({
            type: itemType,
            value: item,
            index: 0,
            state: 0,
          });
        } else {
          // Finished processing array
          hashChunk(smallBuffer[3]); // ']'
          current.state = 2;
        }
      } else if (current.type === TYPE_OBJECT) {
        const keys = current.keys!;

        if (current.index > 0) {
          hashChunk(smallBuffer[5]); // ','
        }

        if (current.index < keys.length) {
          const key = keys[current.index++]!;
          hashChunk(key);
          hashChunk(smallBuffer[4]); // ':'

          const item = current.value[key];
          const itemType =
            item === null || typeof item !== 'object'
              ? TYPE_PRIMITIVE
              : Array.isArray(item)
                ? TYPE_ARRAY
                : TYPE_OBJECT;

          // Push the item onto the stack
          stack.push({
            type: itemType,
            value: item,
            index: 0,
            state: 0,
          });
        } else {
          // Finished processing object
          hashChunk(smallBuffer[1]); // '}'
          current.state = 2;
        }
      }
    }
    // Finished with this item
    else {
      stack.pop();
    }
  }

  // Finalize the hash (MurmurHash3 finalization)
  h1 ^= h1 >>> 16;
  h1 = (h1 * 0x85ebca6b) >>> 0;
  h1 ^= h1 >>> 13;
  h1 = (h1 * 0xc2b2ae35) >>> 0;
  h1 ^= h1 >>> 16;

  return h1.toString(16).padStart(8, '0');
}

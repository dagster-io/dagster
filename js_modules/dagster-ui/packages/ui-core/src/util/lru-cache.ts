interface LRUCacheNode<T> {
  key: string;
  value: T;
  prev?: LRUCacheNode<T>;
  next?: LRUCacheNode<T>;
}

export class LRUCache<T> {
  private capacity: number;
  private map: Map<string, LRUCacheNode<T>>;
  private head?: LRUCacheNode<T>;
  private tail?: LRUCacheNode<T>;

  constructor(capacity: number) {
    this.capacity = capacity;
    this.map = new Map();
  }

  get(key: string): T | undefined {
    const node = this.map.get(key);
    if (!node) {
      return undefined;
    }

    this.moveToFront(node);
    return node.value;
  }

  put(key: string, value: T): void {
    let node = this.map.get(key);

    if (node) {
      node.value = value;
      this.moveToFront(node);
    } else {
      if (this.map.size >= this.capacity) {
        this.removeLast();
      }

      node = {key, value};
      this.addToFront(node);
      this.map.set(key, node);
    }
  }

  // Serialize the cache for storage
  toJSON(): {[key: string]: T} {
    const result: {[key: string]: T} = {};
    for (const [key, node] of this.map) {
      result[key] = node.value;
    }
    return result;
  }

  // Deserialize from stored data
  static fromJSON<T>(data: {[key: string]: T}, capacity: number): LRUCache<T> {
    const cache = new LRUCache<T>(capacity);
    for (const key in data) {
      if (data.hasOwnProperty(key)) {
        cache.put(key, data[key] as T);
      }
    }
    return cache;
  }

  private moveToFront(node: LRUCacheNode<T>): void {
    if (node === this.head) {
      return;
    }

    this.removeNode(node);
    this.addToFront(node);
  }

  private addToFront(node: LRUCacheNode<T>): void {
    node.prev = undefined;
    node.next = this.head;

    if (this.head) {
      this.head.prev = node;
    }

    this.head = node;

    if (!this.tail) {
      this.tail = node;
    }
  }

  private removeNode(node: LRUCacheNode<T>): void {
    if (node.prev) {
      node.prev.next = node.next;
    } else {
      this.head = node.next;
    }

    if (node.next) {
      node.next.prev = node.prev;
    } else {
      this.tail = node.prev;
    }
  }

  private removeLast(): void {
    if (!this.tail) {
      return;
    }

    this.map.delete(this.tail.key);
    this.removeNode(this.tail);
  }
}

// Example usage with IndexedDB:
// To store: JSON.stringify(cache.toJSON())
// To load: LRUCache.fromJSON(JSON.parse(storedData), capacity)

export class DeferredCallbackRegistry<TCallbacks extends Record<string, (...args: any[]) => any>> {
  private queue: Array<Partial<TCallbacks>> = [];
  private targetFn: ((callbacks: Partial<TCallbacks>) => void) | null = null;
  private listeners: {[K in keyof TCallbacks]?: Set<NonNullable<TCallbacks[K]>>} = {};

  /**
   * Register the target function that will handle callbacks.
   */
  public register(fn: (callbacks: Partial<TCallbacks>) => void): void {
    this.targetFn = fn;

    // Execute all queued callbacks
    while (true) {
      const callbacks = this.queue.shift();
      if (!callbacks) {
        break;
      }
      fn(callbacks);
    }
  }

  /**
   * Watch with callbacks. Returns an unsubscribe function.
   */
  public watch(callbacks: Partial<TCallbacks>): () => void {
    // Wrap callbacks to ensure unique references
    const wrappedCallbacks: Partial<TCallbacks> = {};
    const addedCallbacks: Array<{key: keyof TCallbacks; callback: (...args: any[]) => any}> = [];

    for (const [key, callback] of Object.entries(callbacks) as Array<
      [keyof TCallbacks, (...args: any[]) => any]
    >) {
      if (callback) {
        const wrapped = (...args: any[]) => callback(...args);
        wrappedCallbacks[key] = wrapped as unknown as TCallbacks[typeof key];

        // Add to listeners
        if (!this.listeners[key]) {
          this.listeners[key] = new Set();
        }
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        this.listeners[key]!.add(wrapped as unknown as TCallbacks[typeof key]);
        this.listeners[key] = new Set(this.listeners[key]);
        addedCallbacks.push({key, callback: wrapped});
      }
    }

    // Either call immediately or queue
    if (this.targetFn) {
      this.targetFn(wrappedCallbacks);
    } else {
      this.queue.push(wrappedCallbacks);
    }

    // Return unsubscribe function
    return () => {
      for (const {key, callback} of addedCallbacks) {
        this.listeners[key]?.delete(callback as TCallbacks[typeof key]);
        this.listeners[key] = new Set(this.listeners[key]);
      }
    };
  }

  /**
   * Get listeners for a specific callback type.
   */
  public getListeners<K extends keyof TCallbacks>(key: K): Set<NonNullable<TCallbacks[K]>> {
    return this.listeners[key] || new Set();
  }

  /**
   * Check if registered.
   */
  public isRegistered(): boolean {
    return this.targetFn !== null;
  }
}

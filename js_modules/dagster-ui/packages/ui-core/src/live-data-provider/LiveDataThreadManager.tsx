import {LiveDataThread, LiveDataThreadID} from './LiveDataThread';
import {BATCH_SIZE} from './util';
import {isDocumentVisible} from '../hooks/useDocumentVisibility';

type Listener<T> = (stringKey: string, data?: T | undefined) => void;

export class LiveDataThreadManager<T> {
  protected static _instance: LiveDataThreadManager<any>;
  private threads: Partial<Record<LiveDataThreadID, LiveDataThread<T>>>;
  private lastFetchedOrRequested: Record<
    string,
    {fetched: number; requested?: undefined} | {requested: number; fetched?: undefined} | null
  >;
  private cache: Record<string, T>;
  private pollRate: number = 30000;
  private listeners: Record<string, undefined | Listener<T>[]>;
  private isPaused: boolean;

  private onSubscriptionsChanged(_allKeys: string[]) {}
  private onUpdatedOrUpdating() {}

  private async queryKeys(_keys: string[]): Promise<Record<string, T>> {
    return {};
  }

  constructor(queryKeys: (keys: string[]) => Promise<Record<string, T>>) {
    this.queryKeys = queryKeys;
    this.lastFetchedOrRequested = {};
    this.cache = {};
    this.threads = {};
    this.listeners = {};
    this.isPaused = false;
  }

  public setPollRate(pollRate: number) {
    this.pollRate = pollRate;
    Object.values(this.threads).forEach((thread) => {
      thread.setPollRate(pollRate);
    });
  }

  // This callback is used by the main provider context to identify which keys we should be listening to run events for.
  public setOnSubscriptionsChangedCallback(
    onSubscriptionsChanged: typeof this.onSubscriptionsChanged,
  ) {
    this.onSubscriptionsChanged = onSubscriptionsChanged;
  }

  // This callback is used by the main provider context as a hook to know when data fetch status has changed
  // for knowing the "oldest data timestamp" shown as a tooltip on our refresh data buttons
  public setOnUpdatingOrUpdated(onUpdatingOrUpdated: typeof this.onUpdatedOrUpdating) {
    this.onUpdatedOrUpdating = onUpdatingOrUpdated;
  }

  public subscribe(key: string, listener: Listener<T>, threadID: LiveDataThreadID = 'default') {
    let _thread = this.threads[threadID];
    if (!_thread) {
      _thread = new LiveDataThread(this, this.queryKeys);
      if (!this.isPaused) {
        _thread.startFetchLoop();
      }
      this.threads[threadID] = _thread;
    }
    this.listeners[key] = this.listeners[key] || [];
    this.listeners[key]!.push(listener);
    if (this.cache[key]) {
      listener(key, this.cache[key]);
    }
    const thread = _thread;
    thread.subscribe(key);
    this.scheduleOnSubscriptionsChanged();
    return () => {
      thread.unsubscribe(key);
      this.scheduleOnSubscriptionsChanged();
    };
  }

  /**
   * Schedule calling onSubscriptionsChanged instead of calling it synchronously in case we're unsubscribing from 1,000+ keys synchronously
   */
  private scheduledOnSubscriptionsChanged: boolean = false;
  private scheduleOnSubscriptionsChanged() {
    if (this.scheduledOnSubscriptionsChanged) {
      return;
    }
    this.scheduledOnSubscriptionsChanged = true;
    requestAnimationFrame(() => {
      this.onSubscriptionsChanged(this.getAllObservedKeys());
      this.scheduledOnSubscriptionsChanged = false;
    });
  }

  /**
   * Removes the lastFetchedOrRequested entries for the keys specified or all keys if none are specified
   * so that the keys are re-eligible for fetching again despite the pollRate.
   */
  public invalidateCache(keys?: string[]) {
    (keys ?? Object.keys(this.lastFetchedOrRequested)).forEach((key) => {
      delete this.lastFetchedOrRequested[key];
    });
  }

  // Function used by threads.
  public determineKeysToFetch(keys: string[]) {
    const keysToFetch: string[] = [];
    const keysWithoutData: string[] = [];
    while (keys.length && keysWithoutData.length < BATCH_SIZE) {
      const key = keys.shift()!;
      const isRequested = !!this.lastFetchedOrRequested[key]?.requested;
      if (isRequested) {
        continue;
      }
      const lastFetchTime = this.lastFetchedOrRequested[key]?.fetched ?? null;
      if (lastFetchTime !== null && Date.now() - lastFetchTime < this.pollRate) {
        continue;
      }
      if (lastFetchTime && isDocumentVisible()) {
        keysToFetch.push(key);
      } else {
        keysWithoutData.push(key);
      }
    }

    // Prioritize fetching keys for which there is no data in the cache
    return keysWithoutData.concat(keysToFetch).slice(0, BATCH_SIZE);
  }

  public areKeysRefreshing(keys: string[]) {
    for (const key of keys) {
      if (!this.lastFetchedOrRequested[key]?.fetched) {
        return true;
      }
    }
    return false;
  }

  private getAllObservedKeys() {
    const threads = Object.values(this.threads);
    return Array.from(new Set(threads.flatMap((thread) => thread.getObservedKeys())));
  }

  public getOldestDataTimestamp() {
    const allKeys = Object.keys(this.listeners).filter((key) => this.listeners[key]?.length);
    let isRefreshing = allKeys.length ? true : false;
    let oldestDataTimestamp = Infinity;
    for (const key of allKeys) {
      if (this.lastFetchedOrRequested[key]?.fetched) {
        isRefreshing = false;
      }
      oldestDataTimestamp = Math.min(
        oldestDataTimestamp,
        this.lastFetchedOrRequested[key]?.fetched ?? Infinity,
      );
    }
    return {
      isRefreshing,
      oldestDataTimestamp: oldestDataTimestamp === Infinity ? 0 : oldestDataTimestamp,
    };
  }

  public _updateCache(data: Record<string, T>) {
    Object.assign(this.cache, data);
  }

  public onDocumentVisiblityChange(isDocumentVisible: boolean) {
    if (isDocumentVisible) {
      if (this.isPaused) {
        this.unpause();
      }
    } else if (!this.isPaused) {
      this.pause();
    }
  }

  private pause() {
    this.isPaused = true;
    Object.values(this.threads).forEach((thread) => {
      thread.stopFetchLoop();
    });
  }

  private unpause() {
    this.isPaused = false;
    Object.values(this.threads).forEach((thread) => {
      thread.startFetchLoop();
    });
  }

  public getCacheEntry(key: string) {
    return this.cache[key];
  }

  public _markKeysRequested(keys: string[]) {
    const requestTime = Date.now();
    keys.forEach((key) => {
      this.lastFetchedOrRequested[key] = {
        requested: requestTime,
      };
    });
    this.onUpdatedOrUpdating();
  }

  public _unmarkKeysRequested(keys: string[]) {
    keys.forEach((key) => {
      delete this.lastFetchedOrRequested[key];
    });
  }

  public _updateFetchedKeys(keys: string[], data: Record<string, T>) {
    const fetchedTime = Date.now();
    keys.forEach((key) => {
      this.lastFetchedOrRequested[key] = {
        fetched: fetchedTime,
      };
      const assetData = data[key];
      if (!assetData) {
        return;
      }
      this.cache[key] = assetData;
      const listeners = this.listeners[key];
      if (!listeners) {
        return;
      }
      listeners.forEach((listener) => {
        listener(key, assetData);
      });
    });
    this.onUpdatedOrUpdating();
  }
}

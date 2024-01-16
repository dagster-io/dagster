import {ApolloClient} from '@apollo/client';

import {LiveDataForNode, tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {isDocumentVisible} from '../hooks/useDocumentVisibility';

import {AssetLiveDataThread, AssetLiveDataThreadID} from './AssetLiveDataThread';
import {BATCH_SIZE} from './util';

type Listener = (stringKey: string, assetData?: LiveDataForNode) => void;

export class AssetLiveDataThreadManager {
  protected static _instance: AssetLiveDataThreadManager;
  private threads: Partial<Record<AssetLiveDataThreadID, AssetLiveDataThread>>;
  private lastFetchedOrRequested: Record<
    string,
    {fetched: number; requested?: undefined} | {requested: number; fetched?: undefined} | null
  >;
  private cache: Record<string, LiveDataForNode>;
  private client: ApolloClient<any>;
  private pollRate: number = 30000;
  private listeners: Record<string, undefined | Listener[]>;
  private isPaused: boolean;

  private onSubscriptionsChanged(_allKeys: string[]) {}
  private onUpdatedOrUpdating() {}

  constructor(client: ApolloClient<any>) {
    this.lastFetchedOrRequested = {};
    this.cache = {};
    this.client = client;
    this.threads = {};
    this.listeners = {};
    this.isPaused = false;
  }

  static getInstance(client: ApolloClient<any>) {
    if (!this._instance) {
      console.log('new instance');
      this._instance = new AssetLiveDataThreadManager(client);
    }
    return this._instance;
  }

  public setPollRate(pollRate: number) {
    this.pollRate = pollRate;
    Object.values(this.threads).forEach((thread) => {
      thread.setPollRate(pollRate);
    });
  }

  // This callback is used by the main provider context to identify which assets we should be listening to run events for.
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

  public subscribe(key: AssetKeyInput, listener: Listener, threadID: AssetLiveDataThreadID) {
    const assetKey = tokenForAssetKey(key);
    let _thread = this.threads[threadID];
    if (!_thread) {
      _thread = new AssetLiveDataThread(this.client, this);
      if (!this.isPaused) {
        _thread.startFetchLoop();
      }
      this.threads[threadID] = _thread;
    }
    this.listeners[assetKey] = this.listeners[assetKey] || [];
    this.listeners[assetKey]!.push(listener);
    if (this.cache[assetKey]) {
      listener(assetKey, this.cache[assetKey]);
    }
    const thread = _thread;
    thread.subscribe(assetKey);
    this.scheduleOnSubscriptionsChanged();
    return () => {
      thread.unsubscribe(assetKey);
      this.scheduleOnSubscriptionsChanged();
    };
  }

  /**
   * Schedule calling onSubscriptionsChanged instead of calling it synchronously in case we're unsubscribing from 1,000+ assets synchronously
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
   * Removes the lastFetchedOrRequested entries for the assetKeys specified or all assetKeys if none are specified
   * so that the assetKeys are re-eligible for fetching again despite the pollRate.
   */
  public refreshKeys(keys?: AssetKeyInput[]) {
    (keys?.map((key) => tokenForAssetKey(key)) ?? Object.keys(this.lastFetchedOrRequested)).forEach(
      (key) => {
        delete this.lastFetchedOrRequested[key];
      },
    );
  }

  // Function used by threads.
  public determineAssetsToFetch(keys: string[]) {
    const assetsToFetch: AssetKeyInput[] = [];
    const assetsWithoutData: AssetKeyInput[] = [];
    while (keys.length && assetsWithoutData.length < BATCH_SIZE) {
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
        assetsToFetch.push({path: key.split('/')});
      } else {
        assetsWithoutData.push({path: key.split('/')});
      }
    }

    // Prioritize fetching assets for which there is no data in the cache
    return assetsWithoutData.concat(assetsToFetch).slice(0, BATCH_SIZE);
  }

  public areKeysRefreshing(assetKeys: AssetKeyInput[]) {
    for (const key of assetKeys) {
      const stringKey = tokenForAssetKey(key);
      if (!this.lastFetchedOrRequested[stringKey]?.fetched) {
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
    const allAssetKeys = Object.keys(this.listeners).filter((key) => this.listeners[key]?.length);
    let isRefreshing = allAssetKeys.length ? true : false;
    let oldestDataTimestamp = Infinity;
    for (const key of allAssetKeys) {
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

  public _updateCache(data: Record<string, LiveDataForNode>) {
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

  public getCacheEntry(key: AssetKeyInput) {
    return this.cache[tokenForAssetKey(key)];
  }

  public _markAssetsRequested(assetKeys: AssetKeyInput[]) {
    const requestTime = Date.now();
    assetKeys.forEach((key) => {
      this.lastFetchedOrRequested[tokenForAssetKey(key)] = {
        requested: requestTime,
      };
    });
    this.onUpdatedOrUpdating();
  }

  public _unmarkAssetsRequested(assetKeys: AssetKeyInput[]) {
    assetKeys.forEach((key) => {
      delete this.lastFetchedOrRequested[tokenForAssetKey(key)];
    });
  }

  public _updateFetchedAssets(assetKeys: AssetKeyInput[], data: Record<string, LiveDataForNode>) {
    const fetchedTime = Date.now();
    assetKeys.forEach((key) => {
      this.lastFetchedOrRequested[tokenForAssetKey(key)] = {
        fetched: fetchedTime,
      };
    });
    Object.entries(data).forEach(([key, assetData]) => {
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

  public static __resetForJest() {
    const instance = AssetLiveDataThreadManager._instance;
    if (instance) {
      instance.cache = {};
      Object.values(instance.threads).forEach((thread) => thread.stopFetchLoop());
      instance.threads = {};
    }
    // @ts-expect-error - its ok
    AssetLiveDataThreadManager._instance = undefined;
  }
}

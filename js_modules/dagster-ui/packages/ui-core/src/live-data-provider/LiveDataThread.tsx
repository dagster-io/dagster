import {LiveDataThreadManager} from './LiveDataThreadManager';
import {BATCHING_INTERVAL} from './util';

export type LiveDataThreadID = 'default' | 'sidebar' | 'asset-graph' | 'group-node';

export class LiveDataThread<T> {
  private isFetching: boolean = false;
  private listenersCount: {[key: string]: number};
  private isLooping: boolean = false;
  private interval?: ReturnType<typeof setTimeout>;
  private manager: LiveDataThreadManager<any>;
  public pollRate: number = 30000;

  protected static _threads: {[key: string]: LiveDataThread<any>} = {};

  private async queryKeys(_keys: string[]): Promise<Record<string, T>> {
    return {};
  }

  constructor(
    manager: LiveDataThreadManager<T>,
    queryKeys: (keys: string[]) => Promise<Record<string, T>>,
  ) {
    this.queryKeys = queryKeys;
    this.listenersCount = {};
    this.manager = manager;
  }

  public setPollRate(pollRate: number) {
    this.pollRate = pollRate;
  }

  public subscribe(key: string) {
    this.listenersCount[key] = this.listenersCount[key] || 0;
    this.listenersCount[key] += 1;
    this.startFetchLoop();
  }

  public unsubscribe(key: string) {
    this.listenersCount[key] -= 1;
    if (this.listenersCount[key] === 0) {
      delete this.listenersCount[key];
    }
    if (this.getObservedKeys().length === 0) {
      this.stopFetchLoop();
    }
  }

  public getObservedKeys() {
    return Object.keys(this.listenersCount);
  }

  public startFetchLoop() {
    if (this.isLooping) {
      return;
    }
    this.isLooping = true;
    const fetch = () => {
      this._batchedQueryKeys();
    };
    setTimeout(fetch, BATCHING_INTERVAL);
    this.interval = setInterval(fetch, 5000);
  }

  public stopFetchLoop() {
    if (!this.isLooping) {
      return;
    }
    this.isLooping = false;
    clearInterval(this.interval);
    this.interval = undefined;
  }

  private async _batchedQueryKeys() {
    const keys = this.manager.determineKeysToFetch(this.getObservedKeys());
    if (!keys.length || this.isFetching) {
      return;
    }
    this.isFetching = true;
    this.manager._markKeysRequested(keys);

    const doNextFetch = () => {
      this.isFetching = false;
      this._batchedQueryKeys();
    };
    try {
      const data = await this.queryKeys(keys);
      this.manager._updateFetchedKeys(keys, data);
      doNextFetch();
    } catch (e) {
      console.error(e);

      if ((e as any)?.message?.includes('500')) {
        // Mark these keys as fetched so that we don't retry them until after the poll interval rather than retrying them immediately.
        // This is preferable because if the keys failed to fetch it's likely due to a timeout due to the query being too expensive and retrying it
        // will not make it more likely to succeed and it would add more load to the database.
        this.manager._updateFetchedKeys(keys, {});
      } else {
        // If it's not a timeout from the backend then lets keep retrying instead of moving on.
        this.manager._unmarkKeysRequested(keys);
      }

      setTimeout(
        () => {
          doNextFetch();
        },
        // If the poll rate is faster than 5 seconds lets use that instead
        Math.min(this.pollRate, 5000),
      );
    }
  }
}

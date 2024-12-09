import {LiveDataScheduler} from './LiveDataScheduler';
import {LiveDataThreadManager} from './LiveDataThreadManager';
import {BATCH_PARALLEL_FETCHES, BATCH_SIZE, threadIDToLimits} from './util';

export type LiveDataThreadID = string;

export class LiveDataThread<T> {
  private listenersCount: {[key: string]: number};
  private activeFetches: number = 0;
  private intervals: ReturnType<typeof setTimeout>[];
  private manager: LiveDataThreadManager<any>;

  private batchSize: number = BATCH_SIZE;
  private parallelFetches: number = BATCH_PARALLEL_FETCHES;
  public pollRate: number = 30000;

  protected static _threads: {[key: string]: LiveDataThread<any>} = {};

  private async queryKeys(_keys: string[]): Promise<Record<string, T>> {
    return {};
  }

  private _scheduler: LiveDataScheduler<T>;

  constructor(
    id: string,
    manager: LiveDataThreadManager<T>,
    queryKeys: (keys: string[]) => Promise<Record<string, T>>,
  ) {
    const limits = threadIDToLimits[id];
    if (limits) {
      this.batchSize = limits.batchSize;
      this.parallelFetches = limits.parallelThreads;
    }
    this.queryKeys = queryKeys;
    this.listenersCount = {};
    this.manager = manager;
    this.intervals = [];
    this._scheduler = new LiveDataScheduler(this);
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
    if (!this.listenersCount[key]) {
      return;
    }
    this.listenersCount[key] -= 1;
    if (this.listenersCount[key] === 0) {
      delete this.listenersCount[key];
    }
    this.stopFetchLoop(false);
  }

  public getObservedKeys() {
    return Object.keys(this.listenersCount);
  }

  public startFetchLoop() {
    this._scheduler.scheduleStartFetchLoop(() => {
      if (this.activeFetches !== this.parallelFetches) {
        requestAnimationFrame(this._batchedQueryKeys);
      }
      if (this.intervals.length !== this.parallelFetches) {
        this.intervals.push(setInterval(this._batchedQueryKeys, 5000));
      }
    });
  }

  public stopFetchLoop(force: boolean) {
    this._scheduler.scheduleStopFetchLoop(() => {
      if (force || this.getObservedKeys().length === 0) {
        this.intervals.forEach((id) => {
          clearInterval(id);
        });
        this.intervals = [];
      }
    });
  }

  private _batchedQueryKeys = async () => {
    if (this.activeFetches >= this.parallelFetches) {
      return;
    }
    const keys = this.manager.determineKeysToFetch(this.getObservedKeys(), this.batchSize);
    if (!keys.length) {
      return;
    }
    this.activeFetches += 1;
    this.manager._markKeysRequested(keys);

    const doNextFetch = () => {
      this.activeFetches -= 1;
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
        doNextFetch,
        // If the poll rate is faster than 5 seconds lets use that instead
        Math.min(this.pollRate, 5000),
      );
    }
  };
}

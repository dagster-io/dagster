import {TimingControls} from './TimingControls';
import type {WorkspaceStatusPoller} from './WorkspaceStatusPoller';
import {ApolloClient, DocumentNode, OperationVariables} from '../../apollo-client';
import {LocationStatusEntryFragment} from './types/WorkspaceQueries.types';
import {clearCachedData, getCachedData, useGetData} from '../../search/useIndexedDBCachedQuery';
const EMPTY_DATA = {};

// A location fetch can fail transiently -- most commonly while a code location is being
// redeployed and its code server is briefly unreachable. The status poller only notifies us when
// a location's versionKey *changes*, so if we drop a failure on the floor nothing will ask us to
// load that location again and the UI keeps rendering the previous deployment's definitions for
// the rest of the session. Retry on our own schedule instead, backing off so that a location
// that is durably broken doesn't hammer the server with an expensive query.
export const RETRY_BASE_INTERVAL = 5000;
export const RETRY_MAX_INTERVAL = 60000;

export abstract class LocationBaseDataFetcher<TData, TVariables extends OperationVariables> {
  private readonly getData: ReturnType<typeof useGetData>;
  private readonly statusPoller: WorkspaceStatusPoller;
  private readonly query: DocumentNode;
  private readonly version: string;

  private data: {[key: string]: TData} = EMPTY_DATA;
  private locationStatuses: Record<string, LocationStatusEntryFragment> = {};
  private subscribers: Set<(data: {[key: string]: TData}) => void>;
  private readonly key: string;
  private loadedFromCache: {[key: string]: boolean};
  private unsubscribe: () => void;
  private failedLocations: Set<string> = new Set();
  private retryAttempt = 0;
  private retryTimeout: ReturnType<typeof setTimeout> | undefined;
  private destroyed = false;
  constructor(args: {
    readonly query: DocumentNode;
    readonly version: string;
    readonly client: ApolloClient<any>;
    readonly statusPoller: WorkspaceStatusPoller;
    readonly getData: ReturnType<typeof useGetData>;
    readonly key: string;
  }) {
    this.key = args.key;
    this.getData = args.getData;
    this.statusPoller = args.statusPoller;
    this.query = args.query;
    this.version = args.version;
    this.subscribers = new Set();
    this.locationStatuses = {};
    this.loadedFromCache = {};
    this.unsubscribe = this.statusPoller.subscribe(
      async ({added, updated, removed, locationStatuses}) => {
        await TimingControls.handleStatusUpdate(async () => {
          this.locationStatuses = locationStatuses;
          const promises = [];
          for (const location of added) {
            promises.push(this.loadFromServer(location));
          }
          for (const location of updated) {
            promises.push(this.loadFromServer(location));
          }
          if (removed.length > 0) {
            for (const location of removed) {
              const nextData = {...this.data};
              delete nextData[location];
              this.data = nextData;
              this.clearFailure(location);
              clearCachedData({
                key: `${this.key}/${location}`,
              });
            }
            this.notifySubscribers();
          }
          await Promise.all(promises);
          this.notifySubscribers();
        });
      },
    );
  }

  abstract getVariables(location: string): TVariables;

  public subscribe(subscriber: (data: {[key: string]: TData}) => void) {
    this.subscribers.add(subscriber);
    if (this.data !== EMPTY_DATA) {
      subscriber(this.data);
    }
    return () => this.subscribers.delete(subscriber);
  }

  private async loadFromCache(name: string) {
    if (this.loadedFromCache[name] || this.data[name]) {
      return;
    }
    this.loadedFromCache[name] = true;
    const cachedData = await getCachedData<TData>({
      key: `${this.key}/${name}`,
      version: this.version,
    });
    if (cachedData) {
      if (!this.data[name]) {
        const nextData = {...this.data};
        nextData[name] = cachedData;
        this.data = nextData;
        this.notifySubscribers();
      } else {
        // If the data is already set then we loaded real data before the cached data was loaded so lets ignore it.
      }
    }
  }

  abstract getVersion(data: TData): string;

  private async loadFromServer(location: string) {
    await this.loadFromCache(location);
    if (!this.locationStatuses[location]) {
      // Wait for location statuses to be loaded. If we were retrying this location it no longer
      // exists as far as we know, so stop retrying it.
      this.clearFailure(location);
      return;
    }
    if (
      this.data[location] &&
      this.getVersion(this.data[location]) === this.locationStatuses[location].versionKey
    ) {
      // If the version hasn't changed then we don't need to load from the server
      this.clearFailure(location);
      return;
    }
    await TimingControls.loadFromServer(async () => {
      const variables = this.getVariables(location);
      const {data, error} = await this.getData<TData, TVariables>({
        query: this.query,
        key: `${this.key}/${location}`,
        version: this.version,
        variables,
        bypassCache: true,
      });
      if (error) {
        console.error(error);
        this.scheduleRetry(location);
      } else if (data) {
        this.clearFailure(location);
        const nextData = {...this.data};
        nextData[location] = data;
        this.data = nextData;
        this.notifySubscribers();
      } else {
        console.error('No data or error returned from fetchLocationData');
        this.scheduleRetry(location);
      }
    });
  }

  private clearFailure(location: string) {
    this.failedLocations.delete(location);
    if (!this.failedLocations.size) {
      this.retryAttempt = 0;
    }
  }

  private scheduleRetry(location: string) {
    if (this.destroyed) {
      return;
    }
    this.failedLocations.add(location);
    if (this.retryTimeout) {
      // A retry is already armed; it picks up every location in `failedLocations`.
      return;
    }
    const delay = Math.min(RETRY_BASE_INTERVAL * 2 ** this.retryAttempt, RETRY_MAX_INTERVAL);
    this.retryAttempt += 1;
    this.retryTimeout = setTimeout(() => {
      this.retryTimeout = undefined;
      this.retryFailedLocations();
    }, delay);
  }

  private async retryFailedLocations() {
    const locations = Array.from(this.failedLocations);
    if (this.destroyed || !locations.length) {
      return;
    }
    // Each attempt that fails again calls `scheduleRetry`, which re-arms the timer, so the retry
    // loop keeps going (with a longer delay each time) until the location loads or goes away.
    await Promise.all(locations.map((location) => this.loadFromServer(location)));
    this.notifySubscribers();
  }

  private notifySubscribers() {
    for (const subscriber of this.subscribers) {
      subscriber(this.data);
    }
  }

  public destroy() {
    this.destroyed = true;
    this.unsubscribe();
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
      this.retryTimeout = undefined;
    }
  }
}

// WorkspaceStatusPoller implementation as described above.

import {CODE_LOCATION_STATUS_QUERY} from './WorkspaceQueries';
import {
  CodeLocationStatusQuery,
  CodeLocationStatusQueryVariables,
  CodeLocationStatusQueryVersion,
  LocationStatusEntryFragment,
} from './types/WorkspaceQueries.types';
import {getCachedData, useGetData} from '../../search/useIndexedDBCachedQuery';

const POLL_INTERVAL = 5000;

const EMPTY_CHANGES = {added: [], updated: [], removed: []};

export const CODE_LOCATION_STATUS_QUERY_KEY = '/CodeLocationStatusQuery';

export class WorkspaceStatusPoller {
  private statuses: Record<string, LocationStatusEntryFragment> = {};
  private readonly getData: ReturnType<typeof useGetData>;
  private lastChanged: {added: string[]; updated: string[]; removed: string[]} = EMPTY_CHANGES;
  private hasNotifiedOnce = false;
  private key: string;
  private readonly subscribers: Set<
    (args: {
      added: string[];
      updated: string[];
      removed: string[];
      locationStatuses: Record<string, LocationStatusEntryFragment>;
    }) => Promise<void>
  >;
  private interval: NodeJS.Timeout | undefined;
  private setCodeLocationStatusAtom: (status: CodeLocationStatusQuery) => void;
  constructor(args: {
    localCacheIdPrefix: string | undefined;
    getData: ReturnType<typeof useGetData>;
    setCodeLocationStatusAtom: (status: CodeLocationStatusQuery) => void;
  }) {
    this.key = `${args.localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`;
    this.getData = args.getData;
    this.setCodeLocationStatusAtom = args.setCodeLocationStatusAtom;
    this.subscribers = new Set();
    this.loadFromCache();
    this.loadFromServer();
    this.interval = setInterval(() => this.loadFromServer(), POLL_INTERVAL);
  }

  private async loadFromCache() {
    const cachedData = await getCachedData<CodeLocationStatusQuery>({
      key: this.key,
      version: CodeLocationStatusQueryVersion,
    });
    if (cachedData) {
      this.setCodeLocationStatusAtom(cachedData);
    }

    if (cachedData?.locationStatusesOrError.__typename === 'WorkspaceLocationStatusEntries') {
      const statuses = Object.fromEntries(
        cachedData.locationStatusesOrError.entries.map((entry) => [entry.name, entry]),
      );
      if (!Object.keys(this.statuses).length) {
        this.statuses = statuses;
        this.checkForChanges({}, statuses);
      } else {
        // We loaded data from the server before the cache data loaded so lets ignore the cached data
      }
    }
  }

  private async loadFromServer() {
    if (document.visibilityState === 'hidden') {
      return;
    }
    const {data, error} = await this.getData<
      CodeLocationStatusQuery,
      CodeLocationStatusQueryVariables
    >({
      query: CODE_LOCATION_STATUS_QUERY,
      key: this.key,
      version: CodeLocationStatusQueryVersion,
      bypassCache: true,
    });
    if (error) {
      console.error('Error loading code location statuses from server', error);
    } else if (data) {
      this.setCodeLocationStatusAtom(data);
      if (data.locationStatusesOrError.__typename === 'WorkspaceLocationStatusEntries') {
        const nextStatuses = Object.fromEntries(
          data.locationStatusesOrError.entries.map((entry) => [entry.name, entry]),
        );
        await this.checkForChanges(this.statuses, nextStatuses);
      } else {
        console.error('Error loading location statuses from server', data.locationStatusesOrError);
      }
    } else {
      console.error('No data or error returned from loadFromServer');
    }
  }

  private async checkForChanges(
    prevStatuses: Record<string, LocationStatusEntryFragment>,
    nextStatuses: Record<string, LocationStatusEntryFragment>,
  ) {
    const {added, updated} = Object.entries(nextStatuses).reduce(
      (acc, [key, status]) => {
        if (!prevStatuses[key]) {
          acc.added.push(key);
        } else if (status.versionKey !== prevStatuses[key].versionKey) {
          acc.updated.push(key);
        }
        return acc;
      },
      {added: [] as string[], updated: [] as string[]},
    );
    const removed = Object.keys(prevStatuses).filter((key) => !nextStatuses[key]);
    this.statuses = nextStatuses;
    this.lastChanged = {added, updated, removed};
    if (added.length > 0 || updated.length > 0 || removed.length > 0 || !this.hasNotifiedOnce) {
      this.hasNotifiedOnce = true;
      await this.notifySubscribers();
    }
  }

  public subscribe(
    subscriber: (args: {
      added: string[];
      updated: string[];
      removed: string[];
      locationStatuses: Record<string, LocationStatusEntryFragment>;
    }) => Promise<void>,
  ) {
    this.subscribers.add(subscriber);
    if (this.lastChanged !== EMPTY_CHANGES) {
      subscriber({
        ...this.lastChanged,
        locationStatuses: this.statuses,
      });
    }
    return () => this.subscribers.delete(subscriber);
  }

  private async notifySubscribers() {
    await Promise.all(
      Array.from(this.subscribers).map((subscriber) => {
        return subscriber({...this.lastChanged, locationStatuses: this.statuses});
      }),
    );
  }

  public destroy() {
    clearInterval(this.interval);
  }

  public async refetch() {
    await this.loadFromServer();
  }
}

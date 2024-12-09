import type {LiveDataThread} from './LiveDataThread';

/**
 * This exists as a separate class to allow Jest to mock it
 */
export class LiveDataScheduler<T> {
  private thread: LiveDataThread<T>;

  constructor(thread: LiveDataThread<T>) {
    this.thread = thread;
  }
  private _started = new WeakSet();
  private _stopped = new WeakSet();

  public scheduleStartFetchLoop(doStart: () => void) {
    if (this._started.has(this.thread)) {
      return;
    }
    setTimeout(() => {
      doStart();
      this._stopped.delete(this.thread);
    }, 50);
  }

  public scheduleStopFetchLoop(doStop: () => void) {
    if (this._stopped.has(this.thread)) {
      return;
    }
    setTimeout(() => {
      doStop();
      this._stopped.delete(this.thread);
    }, 50);
  }
}

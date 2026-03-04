import type {LiveDataThread} from './LiveDataThread';

/**
 * This exists as a separate class to allow Jest to mock it
 */
export class LiveDataScheduler<T> {
  private thread: LiveDataThread<T>;

  constructor(thread: LiveDataThread<T>) {
    this.thread = thread;
  }
  private _starting = false;
  private _stopping = false;

  public scheduleStartFetchLoop(doStart: () => void) {
    if (this._starting) {
      return;
    }
    this._starting = true;
    setTimeout(() => {
      doStart();
      this._starting = false;
    }, 50);
  }

  public scheduleStopFetchLoop(doStop: () => void) {
    if (this._stopping) {
      return;
    }
    this._stopping = true;
    setTimeout(() => {
      doStop();
      this._stopping = false;
    }, 50);
  }
}

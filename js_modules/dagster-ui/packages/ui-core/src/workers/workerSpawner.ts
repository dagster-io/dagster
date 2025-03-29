import {Worker} from 'shared/workers/Worker.oss';

export function workerSpawner(createWorker: () => Worker) {
  function _createWorker() {
    return createWorker();
  }
  function _terminateWorker(worker: Worker) {
    worker.terminate();
  }
  let nextWorker: Worker | null = _createWorker();
  let currentWorker: Worker | null = null;
  const fn = function spawnNewWorker() {
    // Make sure we only have one worker at a time
    if (currentWorker) {
      _terminateWorker(currentWorker);
    }
    if (!nextWorker) {
      nextWorker = _createWorker();
    }
    currentWorker = nextWorker;
    nextWorker = _createWorker();
    return currentWorker;
  };
  fn.terminate = () => {
    if (currentWorker) {
      _terminateWorker(currentWorker);
      currentWorker = null;
    }
    if (nextWorker) {
      _terminateWorker(nextWorker);
      nextWorker = null;
    }
  };
  return fn;
}

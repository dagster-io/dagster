import {Worker} from 'shared/workers/Worker.oss';
export function workerSpawner(createWorker: () => Worker) {
  let nextWorker: Worker = createWorker();
  let currentWorker: Worker | null = null;
  return function spawnNewWorker() {
    // Make sure we only have one worker at a time
    if (currentWorker) {
      currentWorker.terminate();
    }
    currentWorker = nextWorker;
    nextWorker = createWorker();
    return currentWorker;
  };
}

// How many assets to fetch at once
const urlParams = new URLSearchParams(window.location.search);

const urlLiveDataBatchSize = parseInt(urlParams.get('live-data-batch-size') ?? '0', 10);
const urlLiveDataBatchThreads = parseInt(urlParams.get('live-data-parallel-fetches') ?? '0', 10);

const liveDataBatchSize = urlLiveDataBatchSize ?? 10;
const batchThreads = urlLiveDataBatchThreads ?? 2;

export const BATCH_SIZE = isNaN(liveDataBatchSize) ? 10 : liveDataBatchSize;
export const BATCH_PARALLEL_FETCHES = isNaN(batchThreads) ? 2 : batchThreads;

export const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;
export const SUBSCRIPTION_MAX_POLL_RATE = 2 * 1000;

export const threadIDToLimits = {
  ['AssetHealth' as string]: {
    batchSize: urlLiveDataBatchSize ?? 250,
    parallelThreads: urlLiveDataBatchThreads ?? 4,
  },
};

// How many assets to fetch at once
const urlParams = new URLSearchParams(window.location.search);
const liveDataBatchSize = parseInt(urlParams.get('live-data-batch-size') ?? '10', 10);

export const BATCH_SIZE = isNaN(liveDataBatchSize) ? 10 : liveDataBatchSize;

// Milliseconds we wait until sending a batched query
export const BATCHING_INTERVAL = 250;

export const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;
export const SUBSCRIPTION_MAX_POLL_RATE = 2 * 1000;

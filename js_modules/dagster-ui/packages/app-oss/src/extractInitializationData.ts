export const ELEMENT_ID = 'initialization-data';
export const PREFIX_PLACEHOLDER = '__PATH_PREFIX__';
export const TELEMETRY_PLACEHOLDER = '__TELEMETRY_ENABLED__';
export const LIVE_DATA_POLL_RATE_PLACEHOLDER = '__LIVE_DATA_POLL_RATE__';
export const INSTANCE_ID_PLACEHOLDER = '__INSTANCE_ID__';

let value:
  | {pathPrefix: string; telemetryEnabled: boolean; liveDataPollRate?: number; instanceId: string}
  | undefined = undefined;

// Determine the path prefix value, which is set server-side.
// This value will be used for prefixing paths for the GraphQL
// endpoint and dynamically loaded bundles.
export const extractInitializationData = (): {
  pathPrefix: string;
  telemetryEnabled: boolean;
  liveDataPollRate?: number;
  instanceId: string;
} => {
  if (!value) {
    value = {pathPrefix: '', telemetryEnabled: false, instanceId: ''};
    const element = document.getElementById(ELEMENT_ID);
    if (element) {
      const parsed = JSON.parse(element.innerHTML);
      if (parsed.pathPrefix !== PREFIX_PLACEHOLDER) {
        value.pathPrefix = parsed.pathPrefix;
      }
      if (parsed.telemetryEnabled !== TELEMETRY_PLACEHOLDER) {
        value.telemetryEnabled = parsed.telemetryEnabled;
      }
      if (parsed.liveDataPollRate !== LIVE_DATA_POLL_RATE_PLACEHOLDER) {
        value.liveDataPollRate = parsed.liveDataPollRate;
      }
      if (parsed.instanceId !== INSTANCE_ID_PLACEHOLDER) {
        value.instanceId = parsed.instanceId;
      }
    }
  }
  if (value.telemetryEnabled) {
    const script = document.createElement('script');
    script.defer = true;
    script.async = true;
    script.src = 'https://dagster.io/oss-telemetry.js';
    document.head.appendChild(script);
  }
  return value;
};

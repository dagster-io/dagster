const ELEMENT_ID = 'initialization-data';
const PREFIX_PLACEHOLDER = '__PATH_PREFIX__';
const TELEMETRY_PLACEHOLDER = '__TELEMETRY_ENABLED__';

let value: {pathPrefix: string; telemetryEnabled: boolean} | undefined = undefined;

// Determine the path prefix value, which is set server-side.
// This value will be used for prefixing paths for the GraphQL
// endpoint and dynamically loaded bundles.
export const extractInitializationData = (): {
  pathPrefix: string;
  telemetryEnabled: boolean;
} => {
  if (!value) {
    value = {pathPrefix: '', telemetryEnabled: false};
    const element = document.getElementById(ELEMENT_ID);
    if (element) {
      const parsed = JSON.parse(element.innerHTML);
      console.log(parsed);
      if (parsed.pathPrefix !== PREFIX_PLACEHOLDER) {
        value.pathPrefix = parsed.pathPrefix;
      }
      if (parsed.telemetryEnabled !== TELEMETRY_PLACEHOLDER) {
        value.telemetryEnabled = parsed.telemetryEnabled;
      }
    }
  }
  return value;
};

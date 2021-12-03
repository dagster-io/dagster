const ELEMENT_ID = 'path-prefix';
const PREFIX_PLACEHOLDER = '__PATH_PREFIX__';
const TELEMETRY_PLACEHOLDER = '__TELEMETRY_ENABLED__';

let value: {pathPrefix: string | undefined; telemetryEnabled: boolean | undefined} = {
  pathPrefix: undefined,
  telemetryEnabled: undefined,
};

// Determine the path prefix value, which is set server-side.
// This value will be used for prefixing paths for the GraphQL
// endpoint and dynamically loaded bundles.
export const extractInitializationData = () => {
  if (value === undefined) {
    const element = document.getElementById(ELEMENT_ID);
    if (element) {
      const parsed = JSON.parse(element.innerHTML);
      if (
        parsed.pathPrefix !== PREFIX_PLACEHOLDER &&
        parsed.telemetryEnabled !== TELEMETRY_PLACEHOLDER
      ) {
        value = parsed;
      }
    }
  }
  return value;
};

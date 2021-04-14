const ELEMENT_ID = 'path-prefix';
const PLACEHOLDER = '__PATH_PREFIX__';

let value: string | undefined;

// Determine the path prefix value, which is set server-side.
// This value will be used for prefixing paths for the GraphQL
// endpoint and dynamically loaded bundles.
export const extractPathPrefix = () => {
  if (value === undefined) {
    const element = document.getElementById(ELEMENT_ID);
    if (element) {
      const parsed = JSON.parse(element.innerHTML);
      const parsedPrefix = parsed.pathPrefix;
      if (parsedPrefix !== PLACEHOLDER) {
        value = parsedPrefix;
      }
    }
  }
  return value;
};

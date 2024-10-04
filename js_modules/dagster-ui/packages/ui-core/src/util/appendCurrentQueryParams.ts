export function appendCurrentQueryParams(url: string): string {
  // Create a URL object with the input URL relative to the current origin
  const base: string = window.location.origin;
  let inputUrl: URL;

  try {
    inputUrl = new URL(url, base);
  } catch (error) {
    throw new Error(`Invalid URL provided: ${url}`);
  }

  // Parse current page's query parameters
  const currentParams = new URLSearchParams(window.location.search);

  // Parse input URL's query parameters
  const inputParams = new URLSearchParams(inputUrl.search);

  // Collect unique keys from currentParams
  const currentKeys = new Set<string>();
  currentParams.forEach((_, key) => {
    currentKeys.add(key);
  });

  // Iterate over current query parameters and add them if not present in input URL
  currentKeys.forEach((key) => {
    if (!inputParams.has(key)) {
      const values = currentParams.getAll(key);
      values.forEach((value) => {
        inputParams.append(key, value);
      });
    }
  });

  // Update the search parameters of the input URL
  inputUrl.search = inputParams.toString() ? `?${inputParams.toString()}` : '';

  const ret =
    url.startsWith('/') || !/^https?:\/\//i.test(url)
      ? inputUrl.pathname + inputUrl.search
      : inputUrl.toString();

  // Return the relative or absolute URL with updated query parameters
  return ret;
}

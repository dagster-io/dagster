export const appendApolloQueryParams = (uri: string, params: Record<string, string>) => {
  // Create a URL object with the current origin, though we just need the path and
  // search params.
  const url = new URL(uri, window.location.origin);
  const searchParams = new URLSearchParams(url.search);
  Object.entries(params).forEach(([key, value]) => {
    searchParams.set(key, value);
  });
  return `${url.pathname}?${searchParams.toString()}`;
};

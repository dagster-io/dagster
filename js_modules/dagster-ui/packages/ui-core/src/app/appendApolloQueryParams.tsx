export const appendApolloQueryParams = (uri: string, params: Record<string, string>) => {
  // Create a URL object with the provided uri. If it's already a full URL string, the
  // fallback origin will have no effect. Otherwise, it's a placeholder that allows us to
  // operate on a URL object.
  const fallbackOrigin = window.location.origin;
  const url = new URL(uri, fallbackOrigin);
  const searchParams = new URLSearchParams(url.search);
  Object.entries(params).forEach(([key, value]) => {
    searchParams.set(key, value);
  });

  url.search = searchParams.toString();
  const urlString = url.toString();

  // If the origin is the same as the fallback, remove it so that the returned value
  // is just the path and search params, aiming to match the structure of the input `uri`.
  //Otherwise, we had a full URL already, so return the full URL string.
  return url.origin === fallbackOrigin ? urlString.replace(fallbackOrigin, '') : urlString;
};

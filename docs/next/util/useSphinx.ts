export enum SphinxPrefix {
  API_DOCS = '_apidocs',
  MODULES = '_modules',
}

const SPHINX_PREFIXES = [SphinxPrefix.API_DOCS, SphinxPrefix.MODULES];

export function normalizeSphinxPath(
  asPath: string,
  sphinxPrefixes?: string[],
): {
  sphinxPrefix?: SphinxPrefix;
  asPath: string;
} {
  let detectedPrefix: SphinxPrefix | undefined;
  // first item will be empty string from splitting at first char
  const pathnameParts = asPath.split('/');

  (sphinxPrefixes || []).some((prefix) => {
    if (pathnameParts[1].toLowerCase() === prefix.toLowerCase()) {
      detectedPrefix = prefix as SphinxPrefix;
      pathnameParts.splice(1, 1);
      asPath = pathnameParts.join('/') || '/';
      return true;
    }
    return false;
  });

  return {
    asPath,
    sphinxPrefix: detectedPrefix,
  };
}

export function sphinxPrefixFromPage(page: string | string[]) {
  if (Array.isArray(page)) {
    return normalizeSphinxPath('/' + page.join('/'), SPHINX_PREFIXES);
  }

  return normalizeSphinxPath(page, SPHINX_PREFIXES);
}

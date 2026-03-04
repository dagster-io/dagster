module.exports = async () => {
  // Suppress the "punycode module is deprecated" warning (DEP0040).
  // Several transitive dependencies (node-fetch@2, jsdom@20, typeson-registry)
  // use old versions of tr46 that import the deprecated Node built-in punycode
  // module instead of the userland npm package.
  process.env.NODE_OPTIONS = [
    process.env.NODE_OPTIONS,
    '--disable-warning=DEP0040',
  ]
    .filter(Boolean)
    .join(' ');
};

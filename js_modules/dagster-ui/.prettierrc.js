module.exports = {
  bracketSpacing: false,
  printWidth: 100,
  singleQuote: true,
  trailingComma: 'all',

  // https://github.com/trivago/prettier-plugin-sort-imports
  importOrder: ['^@dagster-io/(.*)$', '^[./]'],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
  importOrderGroupNamespaceSpecifiers: true,
  plugins: ["@trivago/prettier-plugin-sort-imports"]
};

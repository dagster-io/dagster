module.exports = {
  // You might want to additionally set this in monorepos where Next.js app is in a subdir
  root: true,
  extends: ['next', 'prettier'],
  overrides: [
    {
      // Adapt to your needs (e.g. some might want to only override "next.config.js")
      files: ['*.js'],
      // This is the default parser of ESLint
      parser: 'espree',
      parserOptions: {
        ecmaVersion: 2023,
      },
    },
  ],
};

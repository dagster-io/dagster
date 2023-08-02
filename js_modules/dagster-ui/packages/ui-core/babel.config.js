module.exports = {
  presets: [
    ['@babel/preset-env', {targets: {node: 'current'}}],
    '@babel/preset-react',
    '@babel/preset-typescript',
  ],
  plugins: [
    'graphql-tag',
    '@babel/plugin-proposal-nullish-coalescing-operator',
    '@babel/plugin-proposal-optional-chaining',
    '@babel/plugin-proposal-class-properties',
    '@babel/plugin-proposal-private-property-in-object',
    '@babel/plugin-proposal-private-methods',
    'babel-plugin-macros',
  ],
};

// postcss-import inlines @import statements before Next.js's built-in CSS
// processing. This is needed because Next.js vendors a fork of css-loader that
// doesn't support the CSS `@import ... layer()` syntax — it misinterprets
// `layer(name)` as a media query. By inlining imports first, postcss-import
// correctly wraps the imported CSS in `@layer` blocks so Blueprint CSS can be
// placed in a cascade layer and our override styles always win.
// See: https://github.com/vercel/next.js/issues/55763
module.exports = {
  plugins: {
    'postcss-import': {},
  },
};

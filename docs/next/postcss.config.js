module.exports = {
  plugins: [
    'tailwindcss',
    // Need to fix this eventually
    process.env.NODE_ENV === 'production' && false
      ? [
        '@fullhuman/postcss-purgecss',
        {
          content: [
            './pages/**/*.{js,jsx,ts,tsx}',
            './components/**/*.{js,jsx,ts,tsx}',
          ],
          defaultExtractor: (content) => content.match(/[\w-/.:]+(?<!:)/g) || [],
        },
      ]
      : undefined,

    [
      'postcss-preset-env',
      {
        stage: 1,
        features: {
          'focus-within-pseudo-class': false,
        },
      },
    ],
  ],
};

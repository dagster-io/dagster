module.exports = {
  presets: [
    ["@babel/preset-env", { targets: { node: "current" } }],
    "@babel/preset-typescript",
    "react-app"
  ],
  plugins: ["graphql-tag", "@babel/plugin-proposal-optional-chaining"]
};

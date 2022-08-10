/* eslint-disable @typescript-eslint/no-var-requires */

// https://nextjs.org/docs/testing
const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: __dirname,
});

const customJestConfig = {
  moduleDirectories: ['node_modules', '<rootDir>/'],
  testEnvironment: 'node',
};

module.exports = createJestConfig(customJestConfig);

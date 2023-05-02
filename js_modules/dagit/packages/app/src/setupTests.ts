// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

const originalWarn = console.warn.bind(console.warn);
beforeAll(() => {
  console.warn = (msg) =>
    !msg.toString().includes('ReactDOM.render is no longer supported in React 18') &&
    originalWarn(msg);
});
afterAll(() => {
  console.warn = originalWarn;
});

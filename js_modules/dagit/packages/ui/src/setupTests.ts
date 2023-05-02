import 'regenerator-runtime/runtime';
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

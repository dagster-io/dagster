// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

const ignoredErrors = ['ReactDOM.render is no longer supported in React 18'];

function bind(method: 'warn' | 'error', original: any) {
  console[method] = (msg) =>
    ignoredErrors.every((error) => !msg.toString().includes(error)) && original(msg);
}
function unbind(method: 'warn' | 'error', original: any) {
  console[method] = original;
}
const originalWarn = console.warn.bind(console.warn);
const originalError = console.error.bind(console.error);
beforeAll(() => {
  bind('error', originalError);
  bind('warn', originalWarn);
});
afterAll(() => {
  unbind('error', originalError);
  unbind('warn', originalWarn);
});

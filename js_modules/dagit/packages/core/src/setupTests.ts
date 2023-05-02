import '@testing-library/jest-dom';
import 'jest-canvas-mock';
import ResizeObserver from 'resize-observer-polyfill';

// react-markdown and its dependencies are ESM-only, which Jest can't
// currently accommodate. Mock markdown components/functions entirely to
// avoid any imports.
jest.mock('./ui/Markdown');
jest.mock('./ui/markdownToPlaintext');

const originalWarn = console.warn.bind(console.warn);
beforeAll(() => {
  console.warn = (msg) =>
    !msg.toString().includes('ReactDOM.render is no longer supported in React 18') &&
    originalWarn(msg);
});
afterAll(() => {
  console.warn = originalWarn;
});

global.ResizeObserver = ResizeObserver;

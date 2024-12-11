import '@testing-library/jest-dom';
import 'jest-canvas-mock';
import ResizeObserver from 'resize-observer-polyfill';

// react-markdown and its dependencies are ESM-only, which Jest can't
// currently accommodate. Mock markdown components/functions entirely to
// avoid any imports.
jest.mock('./ui/Markdown');
jest.mock('./ui/markdownToPlaintext');

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

global.ResizeObserver = ResizeObserver;

interface MockMessageEvent extends Event {
  data: any;
}

class MockBroadcastChannel {
  name: string = '';
  listeners: Array<(event: MockMessageEvent) => void> = [];

  onmessage: ((this: MockBroadcastChannel, ev: MockMessageEvent) => any) | null = null;
  onmessageerror: ((this: MockBroadcastChannel, ev: MockMessageEvent) => any) | null = null;

  private static _instancesByName: Record<string, MockBroadcastChannel> = {};

  constructor(name: string) {
    if (!MockBroadcastChannel._instancesByName[name]) {
      MockBroadcastChannel._instancesByName[name] = this;
      this.name = name;
      this.listeners = [];
    }
    return MockBroadcastChannel._instancesByName[name]!;
  }

  postMessage(message: any): void {
    const event: MockMessageEvent = {type: 'message', data: message} as any;
    this.listeners.forEach((listener) => listener(event));
    if (this.onmessage) {
      this.onmessage(event);
    }
  }

  addEventListener(
    type: string,
    callback: (event: MockMessageEvent) => void,
    _options?: boolean | AddEventListenerOptions,
  ): void {
    if (type === 'message') {
      this.listeners.push(callback);
    }
  }

  removeEventListener(
    type: string,
    callback: (event: MockMessageEvent) => void,
    _options?: boolean | EventListenerOptions,
  ): void {
    if (type === 'message') {
      this.listeners = this.listeners.filter((listener) => listener !== callback);
    }
  }

  dispatchEvent(event: MockMessageEvent): boolean {
    if (event.type === 'message') {
      this.listeners.forEach((listener) => listener(event));
      if (this.onmessage) {
        this.onmessage(event);
      }
      return true;
    }
    return false;
  }

  close(): void {
    this.listeners = [];
    this.onmessage = null;
    this.onmessageerror = null;
  }
}

(global as any).BroadcastChannel = MockBroadcastChannel;

// eslint-disable-next-line @typescript-eslint/no-require-imports
require('fast-text-encoding');

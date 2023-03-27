import '@testing-library/jest-dom';
import 'jest-canvas-mock';

// react-markdown and its dependencies are ESM-only, which Jest can't
// currently accommodate. Mock markdown components/functions entirely to
// avoid any imports.
jest.mock('./ui/Markdown');
jest.mock('./ui/markdownToPlaintext');

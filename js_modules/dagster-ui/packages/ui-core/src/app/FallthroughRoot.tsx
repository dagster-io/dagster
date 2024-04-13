import {componentStub} from './InjectedComponentContext';

export const FallthroughRoot = componentStub('FallthroughRoot');

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default FallthroughRoot;

import {render} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../../testing/TestProvider';
import {AppContext} from '../AppContext';
import {useExecutionSessionStorage} from '../ExecutionSessionStorage';

let BASE_PATH = '';
const REPO_ADDRESS = {
  name: 'test-name',
  location: 'test-location',
};

const PIPELINE = 'test-pipeline';

const oldKeyFormat = (repoAddress: typeof REPO_ADDRESS, pipelineOrJobName: string) => {
  return `dagit.v2.${repoAddress.name}.${pipelineOrJobName}`;
};

const newKeyFormat = (
  basePath: string,
  repoAddress: typeof REPO_ADDRESS,
  pipelineOrJobName: string,
) => {
  return `dagit.v2.${basePath}-${repoAddress.location}-${repoAddress.name}-${pipelineOrJobName}`;
};

describe('ExecutionSessionStorage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('Migrates old localStorage data from old format', () => {
    const testData = {sessions: {test: 'test'}, current: 'test'};

    let oldFormat;
    let newFormat;

    function TestComponent() {
      const context = React.useContext(AppContext);
      BASE_PATH = context.basePath;

      const didInitializeOldData = React.useRef(false);

      if (!didInitializeOldData.current) {
        oldFormat = oldKeyFormat(REPO_ADDRESS, PIPELINE);
        newFormat = newKeyFormat(BASE_PATH, REPO_ADDRESS, PIPELINE);
        window.localStorage.setItem(oldFormat, JSON.stringify(testData));
        didInitializeOldData.current = true;
      }

      useExecutionSessionStorage(REPO_ADDRESS, PIPELINE);
      return <div />;
    }

    render(
      <TestProvider>
        <TestComponent />
      </TestProvider>,
    );

    // Its at the new key
    expect(JSON.parse(window.localStorage.getItem(newFormat) as any)).toEqual(testData);

    // old key is deleted
    expect(window.localStorage.getItem(oldFormat)).toEqual(null);
  });
});

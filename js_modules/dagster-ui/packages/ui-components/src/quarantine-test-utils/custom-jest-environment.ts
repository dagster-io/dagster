import {Circus} from '@jest/types';
import JSDOMEnvironment from 'jest-environment-jsdom';

import {QuarantinedTestState, isTestQuarantined} from './quarantined-tests';

// Custom JSDOM environment to handle quarantined tests
class CustomJSDOM extends JSDOMEnvironment {
  private failedQuarantinedTests = new Set<string>();

  handleTestEvent = async (event: Circus.Event): Promise<void> => {
    if (
      event.name === 'test_start' &&
      (await isTestQuarantined(getFullTestName(event), QuarantinedTestState.SKIPPED))
    ) {
      event.test.mode = 'skip';
    }

    if (event.name === 'test_fn_failure') {
      const fullTestName = getFullTestName(event);
      if (await isTestQuarantined(fullTestName, QuarantinedTestState.MUTED)) {
        this.failedQuarantinedTests.add(fullTestName);
      }
    }

    if (event.name === 'test_done') {
      if (this.failedQuarantinedTests.has(getFullTestName(event))) {
        event.test.status = 'skip';
      }
    }
  };
}

module.exports = CustomJSDOM;

export function getFullTestName(event: {
  test: {name: string; parent?: {name: string; parent?: any}};
}): string {
  let fullTestName = event.test.name;
  let parent = event.test.parent;

  while (parent && parent.name !== 'ROOT_DESCRIBE_BLOCK') {
    fullTestName = `${parent.name} ${fullTestName}`;
    parent = parent.parent;
  }
  return fullTestName;
}

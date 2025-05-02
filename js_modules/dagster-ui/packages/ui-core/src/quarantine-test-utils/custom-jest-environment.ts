import {Circus} from '@jest/types';
import JSDOMEnvironment from 'jest-environment-jsdom';

import {isTestQuarantined} from './quarantined-tests';

// Custom JSDOM environment to handle quarantined tests
class CustomJSDOM extends JSDOMEnvironment {
  private failedQuarantinedTests = new Set<string>();

  handleTestEvent = async (event: Circus.Event): Promise<void> => {
    if (event.name === 'test_fn_failure') {
      const testName = event.test.name;
      const testFile = event.test.parent?.name;
      const fullTestName = `${testFile} ${testName}`;
      if (await isTestQuarantined(fullTestName)) {
        this.failedQuarantinedTests.add(fullTestName);
      }
    }

    if (event.name === 'test_done') {
      const testName = event.test.name;
      const testFile = event.test.parent?.name;
      if (this.failedQuarantinedTests.has(`${testFile} ${testName}`)) {
        event.test.status = 'skip';
      }
    }
  };
}

module.exports = CustomJSDOM;

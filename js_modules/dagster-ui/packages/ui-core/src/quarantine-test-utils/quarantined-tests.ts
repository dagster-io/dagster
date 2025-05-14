interface TestId {
  scope: string;
  name: string;
}

export const QuarantinedTestState = Object.freeze({
  MUTED: 'muted',
  SKIPPED: 'skipped',
});
export type QuarantinedTestState = (typeof QuarantinedTestState)[keyof typeof QuarantinedTestState];

let mutedQuarantinedTestsCache: Set<string> | null = null;
let skippedQuarantinedTestsCache: Set<string> | null = null;

function testIdToString(testId: TestId): string {
  return `${testId.scope} ${testId.name}`;
}

export async function getQuarantinedTests(state: QuarantinedTestState): Promise<Set<string>> {
  if (state === QuarantinedTestState.MUTED && mutedQuarantinedTestsCache) {
    return mutedQuarantinedTestsCache;
  }

  if (state === QuarantinedTestState.SKIPPED && skippedQuarantinedTestsCache) {
    return skippedQuarantinedTestsCache;
  }

  const quarantinedTests = new Set<string>();

  try {
    const token = process.env.BUILDKITE_TEST_QUARANTINE_TOKEN;
    const orgSlug = process.env.BUILDKITE_ORGANIZATION_SLUG;
    const suiteSlug = process.env.BUILDKITE_TEST_SUITE_SLUG;

    const response = await fetch(
      `https://api.buildkite.com/v2/analytics/organizations/${orgSlug}/suites/${suiteSlug}/tests/${state}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    if (!response.ok) {
      throw new Error(`${response.statusText}`);
    }

    const tests = await response.json();
    for (const test of tests) {
      quarantinedTests.add(
        testIdToString({
          scope: test.scope || '',
          name: test.name || '',
        }),
      );
    }
  } catch (error: unknown) {
    if (error instanceof Error) {
      console.log('Quarantined tests fetch error:', error.message);
    } else {
      console.log('Quarantined tests fetch error:', String(error));
    }
  }

  if (state === QuarantinedTestState.MUTED) {
    mutedQuarantinedTestsCache = quarantinedTests;
  } else if (state === QuarantinedTestState.SKIPPED) {
    skippedQuarantinedTestsCache = quarantinedTests;
  }

  return quarantinedTests;
}

export async function isTestQuarantined(
  testName: string,
  state: QuarantinedTestState,
): Promise<boolean> {
  return (await getQuarantinedTests(state)).has(testName);
}

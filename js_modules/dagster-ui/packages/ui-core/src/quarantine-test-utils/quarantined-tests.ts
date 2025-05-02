interface TestId {
  scope: string;
  name: string;
}

let quarantinedTestsCache: Set<string> | null = null;

function testIdToString(testId: TestId): string {
  return `${testId.scope} ${testId.name}`;
}

export async function getQuarantinedTests(): Promise<Set<string>> {
  if (quarantinedTestsCache) {
    return quarantinedTestsCache;
  }

  const quarantinedTests = new Set<string>();

  try {
    const token = process.env.BUILDKITE_TEST_QUARANTINE_TOKEN;
    const orgSlug = process.env.BUILDKITE_ORGANIZATION_SLUG;
    const suiteSlug = process.env.BUILDKITE_TEST_SUITE_SLUG;

    const response = await fetch(
      `https://api.buildkite.com/v2/analytics/organizations/${orgSlug}/suites/${suiteSlug}/tests/muted`,
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

  quarantinedTestsCache = quarantinedTests;
  return quarantinedTests;
}

export async function isTestQuarantined(testName: string): Promise<boolean> {
  return (await getQuarantinedTests()).has(testName);
}

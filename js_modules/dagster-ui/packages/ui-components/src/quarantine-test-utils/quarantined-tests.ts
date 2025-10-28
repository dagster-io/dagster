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

    /**
     * Fetches all quarantined tests using pagination.
     * The Buildkite API uses Link headers for pagination.
     * Each response may include a Link header with a 'next' URL.
     * We continue fetching until either:
     * 1. No more pages (next URL is null)
     * 2. Timeout is reached (10 seconds)
     */
    let url: string | null =
      `https://api.buildkite.com/v2/analytics/organizations/${orgSlug}/suites/${suiteSlug}/tests/${state}`;
    const startTime = Date.now();
    const timeout = 10000; // 10 seconds in milliseconds

    while (url && Date.now() - startTime < timeout) {
      const response: Response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`${response.statusText}`);
      }

      for (const test of await response.json()) {
        quarantinedTests.add(
          testIdToString({
            scope: test.scope || '',
            name: test.name || '',
          }),
        );
      }

      // Handle pagination using Link header
      const linkHeader = response.headers.get('Link');
      let nextUrl: string | null = null;

      if (linkHeader) {
        const links = linkHeader.split(',');
        for (const link of links) {
          if (link.includes('rel="next"')) {
            const match = link.match(/<([^>]+)>/);
            if (match) {
              nextUrl = match[1] || null;
              break;
            }
          }
        }
      }

      url = nextUrl;
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

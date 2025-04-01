/// Validates the redirects defined in `vercel.json`

const fs = require('fs').promises;

const BASE_URL = 'https://docs-preview.dagster.io';
const SLEEP_DURATION = 1;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function loadRedirects() {
  try {
    const data = await fs.readFile('vercel.json', 'utf8');
    const json = JSON.parse(data);
    return json.redirects;
  } catch (error) {
    console.error(error);
  }
}

async function validateRedirect(url) {
  try {
    const response = await fetch(url, {redirect: 'manual'});
    if (response.status === 200) {
      console.log(`URL ${url} did not redirect: Status ${response.status}`);
    } else {
      console.log(`Redirect to ${response.headers.get('Location')} works: Status ${response.status}`);
    }
  } catch (error) {
    console.error(`Error fetching ${url}: ${error.message}`);
  }
}

// Entrypoint
(async () => {
  const redirects = await loadRedirects();
  for (const redirect of redirects) {
    const url = BASE_URL + redirect.source.replace(/:path\*/g, 'placeholder');
    await validateRedirect(url);
    await sleep(1000);
  }
})();

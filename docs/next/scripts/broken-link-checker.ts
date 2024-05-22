/**
 * Find broken links that `HTTP_404` in documentation.
 *
 * Defaults to `localhost:3001`, but argument can be provided to override.
 *
 * This script can take several minute to run, the command line utiltiy can also be used, however,
 * this script was used to add more granular control over the output.
 *
 *     $ npx broken-link-checker -ro http://localhost:3001/ >> links-3.txt
 *
 */

import {SiteChecker} from 'broken-link-checker';

const baseUrl = process.argv[2] || 'http://localhost:3001/';

const checker: SiteChecker = new SiteChecker(
  {},
  {
    link: (result) => {
      if (result.broken && result.brokenReason === 'HTTP_404') {
        console.log({
          url: result.url.original,
          html_text: result.html.text,
          html_tag: result.html.tag,
        });
      }
    },
  },
);

checker.enqueue(baseUrl, {});

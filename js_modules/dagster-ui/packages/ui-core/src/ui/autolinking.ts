type AutolinkMatcher = {
  // A regexp matching the text that should be linked
  regexp: RegExp;
  // A prefix that should be prepended to the text to create the link URL.
  // If the regexp matches ben@dagsterlabs.com, the prefix would be "mailto:".
  prefix: string;
};

function wrapRangeInNode(range: Range, nodeName: string) {
  const newNode = document.createElement(nodeName);
  try {
    range.surroundContents(newNode);
  } catch (error) {
    newNode.appendChild(range.extractContents());
    range.insertNode(newNode);
  }
  return newNode;
}

// If we're given an enormous text block, give up rather than trying to linkify
// it's contents.
const MAX_ATTEMPTED_TEXT_CONTENT_LENGTH = 1_000_000;

// Test cases: https://regex101.com/r/pD7iS5/4
function buildURLRegex() {
  const commonTlds = [
    'com',
    'org',
    'edu',
    'gov',
    'uk',
    'net',
    'ca',
    'de',
    'jp',
    'fr',
    'au',
    'us',
    'ru',
    'ch',
    'it',
    'nl',
    'se',
    'no',
    'es',
    'mil',
    'ly',
  ];

  const parts = [
    '(',
    // one of:
    '(',
    // This OR block matches any TLD if the URL includes a scheme, and only
    // the top ten TLDs if the scheme is omitted.
    // YES - https://dagsterlabs.ai
    // YES - https://10.2.3.1
    // YES - dagsterlabs.com
    // NO  - dagsterlabs.ai
    '(',
    // scheme, ala https:// (mandatory)
    // '([A-Za-z]{3,9}:(?:\\/\\/))', << more open ended
    '((http|https):(?:\\/\\/))',

    // username:password (optional)
    '(?:[\\-;:&=\\+\\$,\\w]+@)?',

    // one of:
    '(',
    // domain with any tld
    '([a-zA-Z0-9-_]+\\.)*[a-zA-Z0-9][a-zA-Z0-9-_]+\\.[a-zA-Z]{2,11}',

    '|',

    // ip address
    '(?:[0-9]{1,3}\\.){3}[0-9]{1,3}',
    ')',

    '|',

    // scheme, ala https:// (mandatory)
    '((http|https):(?:\\/\\/))',

    // username:password (optional)
    '(?:[\\-;:&=\\+\\$,\\w]+@)?',

    // one of:
    '(',
    // domain with common tld
    `([a-zA-Z0-9-_]+\\.)*[a-zA-Z0-9][a-zA-Z0-9-_]+\\.(?:${commonTlds.join('|')})`,

    '|',

    // ip address
    '(?:[0-9]{1,3}\\.){3}[0-9]{1,3}',
    ')',
    ')',

    // :port (optional)
    '(?::d*)?',
    ')',

    // optionally followed by:
    '(',
    // URL components
    // (last character must not be puncation, hence two groups)
    '(?:[\\+=~%\\/\\.\\w\\-_@:,!]*[\\+~%\\/\\w\\-:_])?',

    // optionally followed by one or more query string ?asd=asd&as=asd type sections
    "(?:\\?[\\-\\+=&;:%@$\\(\\)'\\*\\/~\\!\\.,\\w_]*[\\-\\+=&;~%@\\w_\\/])*",

    // optionally followed by a #search-or-hash section
    "(?:#['\\$\\&\\(\\)\\*\\+,;=\\.\\!\\/\\\\\\w%-?]*[\\/\\\\\\w])?",
    ')?',
    ')',
  ];

  return new RegExp(parts.join(''), 'gi');
}

function runOnTextNode(node: Node, matchers: AutolinkMatcher[]) {
  // Important: This method iterates through the matchers to find the LONGEST match,
  // and then inserts the <a> tag for it and operates on the remaining previous / next
  // siblings.
  //
  // It looks for the longest match so that URLs that contain phone number fragments
  // are parsed as URLs, etc. Here's an example:
  // https://www.zoom.com/j/9158385033
  //
  // We might be able to "order" the regexps carefully to achieve the same result, but
  // that would be pretty fragile and this "longest" algo more clearly expresses the
  // behavior we really want.
  //
  if (node.parentElement) {
    const withinScript = node.parentElement.tagName === 'SCRIPT';
    const withinStyle = node.parentElement.tagName === 'STYLE';
    const withinA = node.parentElement.closest('a') !== null;
    if (withinScript || withinA || withinStyle) {
      return;
    }
  }
  if (!node.textContent) {
    return;
  }
  const nodeTextContentLen = node.textContent.trim().length;
  if (nodeTextContentLen < 4 || nodeTextContentLen > MAX_ATTEMPTED_TEXT_CONTENT_LENGTH) {
    return;
  }

  let longest: {prefix: string; match: RegExpMatchArray} | null = null;
  let longestLength = null;
  for (const {prefix, regexp} of matchers) {
    regexp.lastIndex = 0;
    const match = regexp.exec(node.textContent);
    if (match !== null) {
      if (!longestLength || match[0].length > longestLength) {
        longest = {prefix, match};
        longestLength = match[0].length;
      }
    }
  }

  if (longest) {
    const {prefix, match} = longest;
    const href = `${prefix}${match[0]}`;
    const range = document.createRange();
    range.setStart(node, match.index || 0);
    range.setEnd(node, (match.index || 0) + match[0].length);
    const aTag = wrapRangeInNode(range, 'A') as HTMLAnchorElement;
    aTag.href = href;
    aTag.rel = 'nofollow noreferrer';
    aTag.target = '_blank';
    aTag.title = href;
  }
}

export function autolinkTextContent(el: HTMLElement, options: {useIdleCallback: boolean}) {
  const textWalker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const matchers: AutolinkMatcher[] = [{prefix: '', regexp: buildURLRegex()}];

  if (options.useIdleCallback) {
    const processUntilDeadline = (deadline: {timeRemaining: () => number}) => {
      while (textWalker.nextNode()) {
        runOnTextNode(textWalker.currentNode, matchers);
        if (deadline.timeRemaining() <= 0) {
          queueIdleCallback();
          return;
        }
      }
    };
    const queueIdleCallback = () => {
      if ('useIdleCallback' in window) {
        window.requestIdleCallback(processUntilDeadline, {timeout: 500});
      } else {
        // If the browser does not support requestIdleCallback but this behavior was requested,
        // set a timeout to ensure we don't block the event loop and then run the fn for a max
        // of 500ms before exiting.
        setTimeout(() => {
          const start = Date.now();
          processUntilDeadline({timeRemaining: () => 500 - (Date.now() - start)});
        }, 100);
      }
    };

    queueIdleCallback();
  } else {
    while (textWalker.nextNode()) {
      runOnTextNode(textWalker.currentNode, matchers);
    }
  }
}

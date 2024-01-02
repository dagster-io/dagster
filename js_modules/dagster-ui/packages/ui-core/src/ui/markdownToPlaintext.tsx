import LRUCache from 'lru-cache';
import {remark} from 'remark';
import gfm from 'remark-gfm';
import strip from 'strip-markdown';

const Remark = remark().use(gfm).use(strip);

const markdownCache = new LRUCache<string, string>({max: 500});
export const markdownToPlaintext = (md: string) => {
  // Compile the Markdown file to plain text:
  const cached = markdownCache.get(md);
  if (cached) {
    return cached;
  }

  // Clean up escaping left behind.
  const str = Remark.processSync(md).toString().replace(/\\/g, '').trim();
  markdownCache.set(md, str);

  return str;
};

import LRUCache from 'lru-cache';
import remark from 'remark';
import gfm from 'remark-gfm';
import toPlainText from 'remark-plain-text';

const Remark = remark()
  .use(gfm)
  .use(toPlainText as any);
const markdownCache = new LRUCache<string, string>({max: 500});
export const markdownToPlaintext = (md: string) => {
  // Compile the Markdown file to plain text:
  const cached = markdownCache.get(md);
  if (cached) {
    return cached;
  }
  const str = Remark.processSync(md).toString();
  markdownCache.set(md, str);
  return str;
};

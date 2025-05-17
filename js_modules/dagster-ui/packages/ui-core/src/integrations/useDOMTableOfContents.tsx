import {useEffect, useRef, useState} from 'react';

type TOCEntry = {
  id: string;
  label: string;
  level: number;
};

export function useDOMTableOfContents() {
  const markdownRef = useRef<HTMLDivElement | null>(null);
  const [tableOfContents, setTableOfContents] = useState<TOCEntry[]>([]);

  useEffect(() => {
    if (!markdownRef.current) {
      return;
    }
    const callback = () => {
      if (!markdownRef.current) {
        return;
      }

      const walker = document.createTreeWalker(markdownRef.current, NodeFilter.SHOW_ELEMENT, {
        acceptNode: (node) =>
          /^H[1-6]$/.test(node.nodeName) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP,
      });

      const toc: TOCEntry[] = [];

      while (walker.nextNode()) {
        const heading = walker.currentNode as HTMLElement;
        const level = parseInt(heading.nodeName.substring(1), 10);
        const entry: TOCEntry = {
          id: heading.id,
          label: heading.textContent || '',
          level,
        };
        toc.push(entry);
      }

      setTableOfContents(toc);
    };

    const observer = new MutationObserver(callback);
    observer.observe(markdownRef.current, {childList: true, subtree: true});
    callback();

    return () => {
      observer.disconnect();
    };
  }, [markdownRef.current]);

  return {markdownRef, tableOfContents};
}

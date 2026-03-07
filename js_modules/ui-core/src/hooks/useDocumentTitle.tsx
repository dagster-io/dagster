import {useEffect} from 'react';

export const useDocumentTitle = (title: string) => {
  useEffect(() => {
    const currentTitle = document.title;
    document.title = title;
    return () => {
      document.title = currentTitle;
    };
  }, [title]);
};

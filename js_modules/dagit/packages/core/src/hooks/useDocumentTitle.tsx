import * as React from 'react';

export const useDocumentTitle = (title: string) => {
  React.useEffect(() => {
    const currentTitle = document.title;
    document.title = title;
    return () => {
      document.title = currentTitle;
    };
  }, [title]);
};

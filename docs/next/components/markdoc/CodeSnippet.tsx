import React, { useState, useEffect } from 'react';
import { Fence } from './FencedCodeBlock';

interface CodeSnippetProps {
  file: string;
  lang: string;
  lines?: string;
  startafter?: string;
  endbefore?: string;
  dedent?: number;
  trim?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

const fetchSnippet = async (params: CodeSnippetProps) => {
  const queryParams = new URLSearchParams({
    file: params.file,
    ...(params.lines && { lines: params.lines }),
    ...(params.startafter && { startafter: params.startafter }),
    ...(params.endbefore && { endbefore: params.endbefore }),
    ...(params.dedent && { dedent: params.dedent.toString() }),
    ...(params.trim !== undefined && { trim: params.trim.toString() }),
  });

  const response = await fetch(`${API_BASE_URL}/api/code-snippet?${queryParams}`);
  if (!response.ok) {
    throw new Error('Failed to fetch snippet');
  }
  return response.text();
};

export const CodeSnippet: React.FC<CodeSnippetProps> = (props) => {
  const [snippet, setSnippet] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const data = await fetchSnippet(props);
        setSnippet(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [props]);

  if (isLoading) return <div>Loading snippet...</div>;
  if (error) return <div>Error: {error}</div>;

  return <Fence data-language={props.lang}>{snippet}</Fence>;
};

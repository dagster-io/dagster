export type StatusAndMessage = {
  type: 'warning' | 'spinner';
  content: string | JSX.Element;
};

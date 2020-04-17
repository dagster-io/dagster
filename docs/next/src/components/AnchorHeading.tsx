import React, { useEffect } from 'react';
import { useAnchorHeadingsActions } from 'hooks/AnchorHeadings';

type AnchorHeadingProps = (
  | JSX.IntrinsicElements['h1']
  | JSX.IntrinsicElements['h2']
  | JSX.IntrinsicElements['h3']
  | JSX.IntrinsicElements['h4']
  | JSX.IntrinsicElements['h5']
  | JSX.IntrinsicElements['h6']
) & {
  tag?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
  href?: string;
  hrefTitle?: string;
};

const AnchorHeading: React.FC<AnchorHeadingProps> = ({
  tag: Tag = 'h1',
  children,
  href,
  hrefTitle,
  ...props
}) => {
  const { addAnchorHeading, removeAnchorHeading } = useAnchorHeadingsActions();

  let localHref: string = '#';
  if (href) localHref = href;
  else if (typeof children === 'string')
    localHref = `#${(children as string)
      .toLowerCase()
      .trim()
      // Remove special characters
      .replace(/[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/gi, '')
      .split(' ')
      .join('-')}`;

  useEffect(() => {
    const title =
      hrefTitle || typeof children === 'string' ? (children as string) : '';

    if (!localHref) return;
    addAnchorHeading({ href: localHref, title, element: Tag });

    return () => {
      if (!localHref) return;
      removeAnchorHeading({ href: localHref });
    };
  }, []);

  return (
    <Tag id={localHref.replace('#', '')} {...props}>
      {children}
      {localHref ? (
        <a href={localHref} className="headerlink" title={hrefTitle}>
          ¶
        </a>
      ) : null}
    </Tag>
  );
};

export default AnchorHeading;

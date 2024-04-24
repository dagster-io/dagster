import cx from 'classnames';

interface Props {
  id: string;
  level?: number;
  children: React.ReactNode;
  className: string;
}

export const Heading = ({id, level = 1, children, className}: Props) => {
  const props = {
    id,
    className: cx('heading', className),
    children: (
      <>
        {children}
        <a className="no-underline group" href={`#${id}`}>
          <span className="ml-2 text-gray-200 hover:text-gray-800 hover:underline">#</span>
        </a>
      </>
    ),
  };

  switch (level) {
    case 1:
      return <h1 {...props} />;
    case 2:
      return <h2 {...props} />;
    case 3:
      return <h3 {...props} />;
    case 4:
      return <h4 {...props} />;
    case 5:
      return <h5 {...props} />;
    case 6:
      return <h6 {...props} />;
  }
};

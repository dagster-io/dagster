import cx from 'classnames';

export const Button = ({
  link,
  style = 'primary',
  children,
}: {
  children: any;
  link: string;
  style?: 'primary' | 'secondary' | 'blurple';
}) => {
  return (
    <div className="h-full flex justify-center items-center">
      <a
        href={link}
        className={cx(
          'text-sm lg:text-base select-none text-center py-2 px-4 rounded-xl transition hover:no-underline cursor-pointer',
          style === 'primary' && 'bg-gable-green text-white hover:bg-gable-green-darker',
          style === 'secondary' &&
            'border text-gable-green hover:text-gable-green-darker hover:border-gable-green',
          style === 'blurple' && 'bg-blurple text-white hover:bg-blurple-darker',
        )}
      >
        {children}
      </a>
    </div>
  );
};

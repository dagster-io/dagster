import Link from 'next/link';

const NavButtonGroup: React.FunctionComponent<{
  prevText?: string;
  prevLink?: string;
  nextText?: string;
  nextLink?: string;
}> = ({ prevText, prevLink, nextText, nextLink }) => {
  return (
    <div className="py-8">
      {prevText && prevLink && (
        <Link href={prevLink}>
          <a>
            <button className="bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded float-left">
              &laquo; {prevText}{' '}
            </button>
          </a>
        </Link>
      )}
      {nextText && nextLink && (
        <Link href={nextLink}>
          <a>
            <button className="bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded float-right">
              {nextText} &raquo;
            </button>
          </a>
        </Link>
      )}
    </div>
  );
};

export default NavButtonGroup;

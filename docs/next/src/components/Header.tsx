import CommunityLinks from './CommunityLinks';
import Search from './Search';

type HeaderProps = {
  onMobileToggleNavigationClick: () => void;
};

const Header: React.FC<HeaderProps> = ({ onMobileToggleNavigationClick }) => {
  return (
    <nav className="bg-white border-b border-gray-200 shadow fixed left-0 right-0 h-16 z-10">
      <div className="mx-auto px-2 sm:px-4 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex px-2 lg:px-0">
            <div className="flex-shrink-0 flex items-center">
              <img
                className="block mt-2 lg:hidden h-8 w-auto"
                src="/assets/logos/small.png"
                alt="Logo"
              />
              <img
                className="hidden mt-2 lg:block h-8 w-auto"
                src="/assets/logos/large.png"
                alt="Logo"
              />
            </div>
            <div className="ml-6 flex">
              <a
                href="#"
                className="inline-flex items-center px-1 pt-1 border-b-2 border-indigo-500 text-sm font-medium leading-5 text-gray-900 focus:outline-none focus:border-indigo-700 transition duration-150 ease-in-out"
              >
                Docs
              </a>
              <a
                href="#"
                className="ml-2 lg:ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                Blog
              </a>
              <a
                href="#"
                className="ml-2 lg:ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                Community
              </a>
            </div>
          </div>
          <Search />
          <div className="flex items-center lg:hidden">
            <button
              onClick={() => onMobileToggleNavigationClick()}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:text-gray-500 transition duration-150 ease-in-out"
            >
              {/* <!-- Icon when menu is closed. -->
          <!-- Menu open: "hidden", Menu closed: "block" --> */}
              <svg
                className="block h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              {/* <!-- Icon when menu is open. -->
          <!-- Menu open: "block", Menu closed: "hidden" --> */}
              <svg
                className="hidden h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="hidden lg:ml-4 lg:flex lg:items-center">
            <CommunityLinks className="w-40" />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Header;

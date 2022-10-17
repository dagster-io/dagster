import cx from 'classnames';
import {JoinSlackButton} from 'components/JoinSlackButton';
import * as React from 'react';
import {useState} from 'react';

import {SignInButton} from './SignInButton';

const COLLAPSING_PX = 0; //-80 if promo banner is hidden

const Header = ({openMobileDocsMenu}) => {
  const [isMobileHeaderOpen, setIsMobileHeaderOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const lastScrollY = React.useRef(0);
  const headerBgRef = React.createRef<HTMLDivElement>();
  const headerRef = React.createRef<HTMLDivElement>();

  React.useEffect(() => {
    const handler = () => {
      if (!headerRef.current || !headerBgRef.current) {
        return;
      }
      const dy = window.scrollY - lastScrollY.current;

      const alpha = Math.min(Math.max(0, (window.scrollY - 30) / 70), 0.98);
      headerBgRef.current.style.opacity = `${alpha}`;

      const targetTop = dy < 0 || window.scrollY < 30 ? 0 : COLLAPSING_PX;
      const currentTop = Number(headerRef.current.style.top.replace('px', ''));

      if (targetTop !== currentTop) {
        headerRef.current.style.top = `${Math.min(0, Math.max(COLLAPSING_PX, currentTop - dy))}px`;
      }

      lastScrollY.current = window.scrollY;

      if (window.scrollY > 0) {
        setIsCollapsed(true);
      } else {
        setIsCollapsed(false);
      }
    };

    document.addEventListener('scroll', handler);
    handler();
    return () => {
      document.removeEventListener('scroll', handler);
    };
  }, [headerRef, headerBgRef]);

  return (
    <div
      ref={headerRef}
      className={cx(
        'fixed top-0  w-full z-50 px-2 lg:px-10 flex flex-col tracking-wide transition-all',
        {
          'p-0 transition': isCollapsed,
          'p-2 transition': !isCollapsed,
        },
      )}
    >
      <div className="absolute z-0 inset-0 bg-white shadow-sm" ref={headerBgRef} />
      <div className="hidden md:block" />
      <nav className="z-10 flex justify-between items-center text-gable-green px-4">
        <div className="flex items-center lg:hidden z-50">
          {/* Mobile docs menu button */}
          <button
            onClick={openMobileDocsMenu}
            className="inline-flex items-center bg-white bg-opacity-50 justify-center p-2 rounded-md text-gable-green hover:text-gable-green-darker hover:bg-opacity-100 focus:outline-none focus:bg-opacity-100 focus:text-gray-500 transition duration-150 ease-in-out"
          >
            <svg className="block h-6 w-6" fill="currentColor" viewBox="0 0 48 48">
              <path d="M28 19.3V16.9Q29.65 16.2 31.375 15.85Q33.1 15.5 35 15.5Q36.3 15.5 37.55 15.7Q38.8 15.9 40 16.2V18.4Q38.8 17.95 37.575 17.725Q36.35 17.5 35 17.5Q33.1 17.5 31.35 17.975Q29.6 18.45 28 19.3ZM28 30.3V27.85Q29.65 27.15 31.375 26.825Q33.1 26.5 35 26.5Q36.3 26.5 37.55 26.7Q38.8 26.9 40 27.2V29.4Q38.8 28.95 37.575 28.725Q36.35 28.5 35 28.5Q33.1 28.5 31.35 28.95Q29.6 29.4 28 30.3ZM28 24.8V22.4Q29.65 21.7 31.375 21.35Q33.1 21 35 21Q36.3 21 37.55 21.2Q38.8 21.4 40 21.7V23.9Q38.8 23.45 37.575 23.225Q36.35 23 35 23Q33.1 23 31.35 23.475Q29.6 23.95 28 24.8ZM12.4 33Q15.1 33 17.625 33.625Q20.15 34.25 22.6 35.5V14.15Q20.35 12.65 17.725 11.825Q15.1 11 12.4 11Q10.5 11 8.675 11.475Q6.85 11.95 5 12.65Q5 12.65 5 12.65Q5 12.65 5 12.65V34.35Q5 34.35 5 34.35Q5 34.35 5 34.35Q6.55 33.65 8.525 33.325Q10.5 33 12.4 33ZM25.6 35.5Q28.1 34.25 30.5 33.625Q32.9 33 35.6 33Q37.5 33 39.525 33.3Q41.55 33.6 43 34.1Q43 34.1 43 34.1Q43 34.1 43 34.1V12.65Q43 12.65 43 12.65Q43 12.65 43 12.65Q41.3 11.8 39.4 11.4Q37.5 11 35.6 11Q32.9 11 30.375 11.825Q27.85 12.65 25.6 14.15ZM24.1 40Q21.55 38.1 18.55 37.075Q15.55 36.05 12.4 36.05Q10.55 36.05 8.8 36.5Q7.05 36.95 5.3 37.6Q4.15 38.15 3.075 37.45Q2 36.75 2 35.45V12.3Q2 11.55 2.35 10.925Q2.7 10.3 3.4 9.95Q5.5 8.95 7.775 8.475Q10.05 8 12.4 8Q15.55 8 18.525 8.85Q21.5 9.7 24.1 11.45Q26.65 9.7 29.575 8.85Q32.5 8 35.6 8Q37.95 8 40.2 8.475Q42.45 8.95 44.55 9.95Q45.25 10.3 45.625 10.925Q46 11.55 46 12.3V35.45Q46 36.85 44.875 37.575Q43.75 38.3 42.65 37.6Q40.95 36.9 39.2 36.475Q37.45 36.05 35.6 36.05Q32.45 36.05 29.55 37.1Q26.65 38.15 24.1 40ZM13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Q13.8 23.55 13.8 23.55Z" />
            </svg>
          </button>
        </div>
        <a
          href="https://dagster.io"
          className="flex-shrink-0 flex items-center z-50 w-9/12 justify-center lg:justify-start lg:w-3/12"
        >
          <img
            className={cx('block h-14 py-3 sm:py-0 transition-all', {
              'sm:h-6': isCollapsed,
              'sm:h-8': !isCollapsed,
            })}
            src="/assets/logos/dagster_logo_primary.svg"
            alt="Dagster logo"
          />
        </a>
        <div
          className={cx(
            'hidden lg:flex my-1  text-gable-green gap-0 w-10/12 md:w-6/12 justify-center transition-all',
            {
              'text-base': isCollapsed,
              'text-lg': !isCollapsed,
            },
          )}
        >
          <a
            href="https://dagster.io/platform"
            className="whitespace-nowrap py-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Platform
          </a>
          <a
            href="https://dagster.io/cloud"
            className="whitespace-nowrap py-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Cloud{' '}
            <div
              className="inline-block text-sm border border-dotted border-gray-700 rounded-xl p-1"
              style={{lineHeight: 1, transform: 'translate(5px, -2px)'}}
            >
              New
            </div>
          </a>
          <a
            href="https://dagster.io/pricing"
            className="py-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Pricing
          </a>
          <a
            href="https://dagster.io/blog"
            className="py-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Blog
          </a>
          <a
            href="https://dagster.io/community"
            className="hidden xl:block py-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Community
          </a>
          <a
            href="/"
            className="py-2 rounded-xl px-4 hover:text-gable-green-darker hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent bg-lavender bg-opacity-100"
          >
            Docs
          </a>
        </div>
        <div
          className={cx(
            'hidden lg:flex my-1  text-gable-green gap-1 w-36 lg:w-3/12 justify-end transition-all',
            {
              'text-base': isCollapsed,
              'text-lg': !isCollapsed,
            },
          )}
        >
          <SignInButton />

          <JoinSlackButton icon={true} />

          <div className="self-center">
            <a
              href="https://github.com/dagster-io/dagster"
              className="px-4 py-1 border border-gable-green cursor-pointer bg-lavender bg-opacity-0 hover:bg-opacity-50 hover:border-opacity-0 inline-flex gap-2 leading-8 items-center rounded-full whitespace-nowrap transition"
            >
              <img className="w-6" src="/assets/logos/github.svg" /> Star us
            </a>
          </div>
          <div className="self-center">
            <a
              href="https://dagster.cloud/signup"
              className="hidden 3xl:inline-flex px-4 py-1 border border-blurple bg-blurple cursor-pointer hover:bg-blurple-darker text-white gap-2 leading-8 items-center rounded-full whitespace-nowrap transition"
            >
              Try Dagster Cloud
            </a>
          </div>
        </div>
        <div></div>

        <div className="flex items-center lg:hidden z-50">
          {/* Mobile menu button */}
          <button
            onClick={() => {
              setIsMobileHeaderOpen(!isMobileHeaderOpen);
            }}
            className="inline-flex items-center bg-white bg-opacity-50 justify-center p-2 rounded-md text-gable-green hover:text-gable-green-darker hover:bg-opacity-100 focus:outline-none focus:bg-opacity-100 focus:text-gray-500 transition duration-150 ease-in-out"
          >
            {/* Menu open: "hidden", Menu closed: "block" */}
            <svg className="block h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            {/* Menu open: "block", Menu closed: "hidden" */}
            <svg className="hidden h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        {/*
          Mobile menu, toggle classes based on menu state.

          Open: "block", closed: "hidden"
        */}
        <div
          className={`${
            isMobileHeaderOpen ? 'block' : 'hidden'
          } lg:hidden pb-2 absolute bg-white w-full top-0 left-0 right-0 pt-20 px-6 shadow-xl`}
        >
          <div className="pt-2 pb-3">
            <a
              href="https://dagster.io/platform"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Platform
            </a>
            <a
              href="https://dagster.io/cloud"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Cloud
            </a>
            <a
              href="https://dagster.io/pricing"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Pricing
            </a>
            <a
              href="https://dagster.io/blog"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Blog
            </a>
            <a
              href="https://dagster.io/community"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Community
            </a>
            <a
              href="/"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Docs
            </a>
            <a
              href="https://dagster.io/contact"
              className="my-0 block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Contact Sales
            </a>
            <hr className="my-2" />
            <a
              href="https://dagster.cloud"
              className="block mb-4 px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Sign in
            </a>
            <a
              href="https://dagster.io//dagster.cloud/signup"
              className="px-6 py-2 border text-lg border-gable-green cursor-pointer bg-transparent hover:bg-gable-green hover:text-white inline-flex gap-2 leading-8 items-center rounded-full whitespace-nowrap transition"
            >
              Try Dagster Cloud
            </a>
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Header;

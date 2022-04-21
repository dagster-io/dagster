import { useRouter } from "next/router";
import * as React from "react";
import { useState } from "react";
import { JoinSlackButton } from "./JoinSlackButton";

const COLLAPSING_PX = -16;

const Header = () => {
  const [isMobileHeaderOpen, setIsMobileHeaderOpen] = useState(false);

  const lastScrollY = React.useRef(0);
  const headerBgRef = React.createRef<HTMLDivElement>();
  const headerRef = React.createRef<HTMLDivElement>();

  React.useEffect(() => {
    const handler = () => {
      if (!headerRef.current || !headerBgRef.current) return;
      const dy = window.scrollY - lastScrollY.current;

      const alpha = Math.min(Math.max(0, (window.scrollY - 100) / 70), 1);
      headerBgRef.current.style.opacity = `${alpha}`;

      const targetTop = dy < 0 || window.scrollY < 100 ? 0 : COLLAPSING_PX;
      const currentTop = Number(headerRef.current.style.top.replace("px", ""));
      if (targetTop !== currentTop) {
        headerRef.current.style.top = `${Math.min(
          0,
          Math.max(COLLAPSING_PX, currentTop - dy)
        )}px`;
      }
      lastScrollY.current = window.scrollY;
    };

    document.addEventListener("scroll", handler);
    handler();
    return () => {
      document.removeEventListener("scroll", handler);
    };
  }, [headerRef, headerBgRef]);

  return (
    <div
      className="fixed top-0 pt-6 pb-2 w-full z-50 px-2 lg:px-10 flex flex-col"
      ref={headerRef}
    >
      <div
        className="absolute z-0 inset-0 bg-white shadow-sm"
        ref={headerBgRef}
      />

      <div className="hidden md:block" />

      <nav className="z-10 flex justify-between items-center text-gable-green px-4">
        <a
          href="https:/dagster.io"
          className="flex-shrink-0 flex items-center z-50"
        >
          <img
            className="block py-3 sm:py-0 h-14 sm:h-auto"
            src="/assets/logos/dagster_logo_primary.svg"
            alt="Dagster logo"
          />
        </a>
        <div className="hidden sm:ml-6 md:flex my-1 text-lg text-gable-green gap-1">
          <a
            href="https:/dagster.io/blog"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Blog
          </a>
          <a
            href="https:/dagster.io/community"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Community
          </a>
          <a
            href="https:/dagster.io/cloud"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Cloud
          </a>
          <a
            href="/"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-lavender bg-opacity-100"
          >
            Docs
          </a>
          <div
            id="social_icons"
            className="space-x-4 ml-4 flex items-center hover:text-gable-green-darker"
          >
            <a href="https://github.com/dagster-io/dagster">
              <svg
                className="h-5 w-5 transition transform hover:opacity-75"
                role="img"
                viewBox="0 0 24 24"
                fill="currentColor"
                xmlns="http://www.w3.org/2000/svg"
              >
                <title>GitHub icon</title>
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
              </svg>
            </a>
            <a href="https://twitter.com/dagsterio">
              <svg
                className="h-5 w-5 transition transform hover:opacity-75"
                role="img"
                viewBox="2 2 20 20"
                fill="currentColor"
                xmlns="http://www.w3.org/2000/svg"
              >
                <title>Twitter icon</title>
                <path d="M22.46,6C21.69,6.35 20.86,6.58 20,6.69C20.88,6.16 21.56,5.32 21.88,4.31C21.05,4.81 20.13,5.16 19.16,5.36C18.37,4.5 17.26,4 16,4C13.65,4 11.73,5.92 11.73,8.29C11.73,8.63 11.77,8.96 11.84,9.27C8.28,9.09 5.11,7.38 3,4.79C2.63,5.42 2.42,6.16 2.42,6.94C2.42,8.43 3.17,9.75 4.33,10.5C3.62,10.5 2.96,10.3 2.38,10C2.38,10 2.38,10 2.38,10.03C2.38,12.11 3.86,13.85 5.82,14.24C5.46,14.34 5.08,14.39 4.69,14.39C4.42,14.39 4.15,14.36 3.89,14.31C4.43,16 6,17.26 7.89,17.29C6.43,18.45 4.58,19.13 2.56,19.13C2.22,19.13 1.88,19.11 1.54,19.07C3.44,20.29 5.7,21 8.12,21C16,21 20.33,14.46 20.33,8.79C20.33,8.6 20.33,8.42 20.32,8.23C21.16,7.63 21.88,6.87 22.46,6Z" />
              </svg>
            </a>
            <a href="https://stackoverflow.com/questions/tagged/dagster">
              <svg
                className="h-5 w-5 transition transform hover:opacity-75"
                role="img"
                viewBox="0 0 24 24"
                fill="currentColor"
                xmlns="http://www.w3.org/2000/svg"
              >
                <title>Stack Overflow icon</title>
                <path d="M18.986 21.865v-6.404h2.134V24H1.844v-8.539h2.13v6.404h15.012zM6.111 19.731H16.85v-2.137H6.111v2.137zm.259-4.852l10.48 2.189.451-2.07-10.478-2.187-.453 2.068zm1.359-5.056l9.705 4.53.903-1.95-9.706-4.53-.902 1.936v.014zm2.715-4.785l8.217 6.855 1.359-1.62-8.216-6.853-1.35 1.617-.01.001zM15.751 0l-1.746 1.294 6.405 8.604 1.746-1.294L15.749 0h.002z" />
              </svg>
            </a>
            <JoinSlackButton header />
          </div>
        </div>

        <div className="flex items-center md:hidden z-50">
          {/* Mobile menu button */}
          <button
            onClick={() => {
              setIsMobileHeaderOpen(!isMobileHeaderOpen);
            }}
            className="inline-flex items-center bg-white bg-opacity-50 justify-center p-2 rounded-md text-gable-green hover:text-gable-green-darker hover:bg-opacity-100 focus:outline-none focus:bg-opacity-100 focus:text-gray-500 transition duration-150 ease-in-out"
          >
            {/* Menu open: "hidden", Menu closed: "block" */}
            <svg
              className="block h-6 w-6"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            {/* Menu open: "block", Menu closed: "hidden" */}
            <svg
              className="hidden h-6 w-6"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 24 24"
            >
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
            isMobileHeaderOpen ? "block" : "hidden"
          } sm:hidden absolute bg-white w-full top-0 left-0 right-0 pt-20 px-6 shadow-xl`}
        >
          <div className="pt-2 pb-3">
            <a
              href="https:/dagster.io"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Home
            </a>
            <a
              href="https:/dagster.io/blog"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Blog
            </a>
            <a
              href="https:/dagster.io/community"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Community
            </a>
            <a
              href="https:/dagster.io/cloud"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Cloud
            </a>
            <a
              href="/"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Docs
            </a>
            <hr className="my-2" />
            <a
              href="https://github.com/dagster-io/dagster"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Github
            </a>
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Header;

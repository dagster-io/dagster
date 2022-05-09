import { useRouter } from "next/router";
import * as React from "react";
import { useState } from "react";
import { JoinSlackButton } from "./JoinSlackButton";
import Icons from "components/Icons";

const COLLAPSING_PX = -16;

const Header = ({ openMobileDocsMenu }) => {
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
      className="fixed top-0 pt-6 pb-2 w-full z-50 px-2 lg:px-10 flex flex-col "
      ref={headerRef}
    >
      <div
        className="absolute z-0 inset-0 bg-white shadow-sm"
        ref={headerBgRef}
      />
      <div className="hidden md:block" />

      <nav className="z-10 flex justify-between items-center text-gable-green px-4">
        <div className="flex items-center lg:hidden z-50">
          {/* Mobile docs menu button */}
          <button
            onClick={openMobileDocsMenu}
            className="inline-flex items-center bg-white bg-opacity-50 justify-center p-2 rounded-md text-gable-green hover:text-gable-green-darker hover:bg-opacity-100 focus:outline-none focus:bg-opacity-100 focus:text-gray-500 transition duration-150 ease-in-out"
          >
            <svg
              className="block h-6 w-6"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
              />
            </svg>
          </button>
        </div>
        <a
          href="https://dagster.io"
          className="flex-shrink-0 flex items-center z-50 w-36 lg:w-3/12"
        >
          <img
            className="block py-3 sm:py-0 h-14 sm:h-8"
            src="/assets/logos/dagster_logo_primary.svg"
            alt="Dagster logo"
          />
        </a>
        <div className="hidden sm:ml-6 md:flex my-1 text-lg text-gable-green gap-1 w-10/12 md:w-6/12 justify-center">
          <a
            href="https://dagster.io/blog"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Blog
          </a>
          <a
            href="https://dagster.io/community"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            Community
          </a>
          <a
            href="/"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-lavender bg-opacity-100"
          >
            Docs
          </a>
          <a
            href="https://dagster.io/cloud"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            <span className="hidden lg:inline">Dagster</span> Cloud
          </a>
        </div>
        <div className="hidden md:flex my-1 text-lg text-gable-green gap-1 w-36 lg:w-3/12 justify-end">
          <a
            href="https://dagster.cloud"
            className="py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent"
          >
            {" "}
            Sign in
          </a>
          <div className="self-center hidden xl:block">
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
          } md:hidden pb-6 absolute bg-white w-full top-0 left-0 right-0 pt-20 px-6 shadow-xl`}
        >
          <div className="pt-2 pb-3">
            <a
              href="https://dagster.io"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Home
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
              href="https://dagster.io/cloud"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Dagster Cloud
            </a>
            <hr className="my-2" />
            <a
              href="https://dagster.cloud"
              className="block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Sign in
            </a>
            <hr className="my-2" />
            <a
              href="https://github.com/dagster-io/dagster"
              className="my-2 block px-4 py-2 rounded-lg text-lg bg-white focus:outline-none hover:bg-lavender transition duration-150 ease-in-out"
            >
              Github
            </a>
            <JoinSlackButton />
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Header;

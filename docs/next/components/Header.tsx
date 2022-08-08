import * as React from "react";
import { useState } from "react";
import { SignInButton } from "./SignInButton";
import { JoinSlackButton } from "components/JoinSlackButton";

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

      const alpha = Math.min(Math.max(0, (window.scrollY - 30) / 70), 1);
      headerBgRef.current.style.opacity = `${alpha}`;

      const targetTop = dy < 0 || window.scrollY < 30 ? 0 : COLLAPSING_PX;
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
          href="https://dagster.io"
          className="flex-shrink-0 flex items-center z-50 w-36 lg:w-3/12"
        >
          <img
            className="block py-3 sm:py-0 h-14 sm:h-8"
            src="/assets/logos/dagster_logo_primary.svg"
            alt="Dagster logo"
          />
        </a>
        <div className="hidden lg:flex my-1 text-lg text-gable-green gap-0 w-10/12 md:w-6/12 justify-center">
          <a
            href="https://dagster.io/platform"
            className={`whitespace-nowrap py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent`}
          >
            Platform
          </a>
          <a
            href="https://dagster.io/cloud"
            className={`whitespace-nowrap py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent`}
          >
            Cloud{" "}
            <div
              className="inline-block text-sm border border-dotted border-gray-700 rounded-xl p-1"
              style={{ lineHeight: 1, transform: "translate(5px, -2px)" }}
            >
              New
            </div>
          </a>
          <a
            href="https://dagster.io/pricing"
            className={`py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent`}
          >
            Pricing
          </a>
          <a
            href="https://dagster.io/blog"
            className={`py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent`}
          >
            Blog
          </a>
          <a
            href="https://dagster.io/community"
            className={`hidden xl:block py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent`}
          >
            Community
          </a>
          <a
            href="/"
            className={`py-2 my-2 rounded-xl px-4 bg-lavender hover:text-gable-green-darker bg-opacity-0 hover:border-2 hover:bg-opacity-50 focus:outline-none focus:text-gable-green-darker transition duration-150 ease-in-out bg-transparent bg-lavender bg-opacity-100`}
          >
            Docs
          </a>
        </div>
        <div className="hidden lg:flex my-1 text-lg text-gable-green gap-1 w-36 lg:w-3/12 justify-end">
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
          } lg:hidden pb-2 absolute bg-white w-full top-0 left-0 right-0 pt-36 px-6 shadow-xl`}
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

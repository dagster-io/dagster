import { promises as fs } from "fs";
import path from "path";

const ApiDocsPage = ({ body, data, page, curr }) => {
  const markup = { __html: body };

  return (
    <>
      <div
        className="flex-1 min-w-0 relative z-0 focus:outline-none pt-8"
        tabIndex={0}
      >
        {/* Start main area*/}
        <div className="py-6 px-4 sm:px-6 lg:px-8 w-full">
          <div className="prose max-w-none" dangerouslySetInnerHTML={markup} />
        </div>
        {/* End main area */}
      </div>
    </>
  );
};

const basePathForVersion = (version: string) => {
  if (version === "master") {
    return path.resolve("content");
  }

  return path.resolve(".versioned_content", version);
};

export async function getServerSideProps({ params, version = "master" }) {
  const { page } = params;

  const basePath = basePathForVersion(version);
  const pathToFile = path.resolve(basePath, "api/sections.json");

  try {
    const buffer = await fs.readFile(pathToFile);
    const {
      api: { apidocs: data },
    } = JSON.parse(buffer.toString());

    let curr = data;
    for (const part of page) {
      curr = curr[part];
    }

    const { body } = curr;

    return {
      props: { body, data, page, curr },
    };
  } catch (err) {
    console.log(err);
    return {
      notFound: true,
    };
  }
}

export default ApiDocsPage;

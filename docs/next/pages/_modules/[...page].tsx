import { promises as fs } from "fs";
import path from "path";

const ApiDocsPage = ({ body, data, page, curr }) => {
  const markup = { __html: body };

  return (
    <div className="flex justify-center mt-10">
      <div
        className="prose prose-sm max-w-none"
        dangerouslySetInnerHTML={markup}
      />
    </div>
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
  const pathToFile = path.resolve(basePath, "api/modules.json");

  try {
    const buffer = await fs.readFile(pathToFile);

    const data = JSON.parse(buffer.toString());

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

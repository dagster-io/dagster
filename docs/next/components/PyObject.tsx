import Link from "next/link";
import data from "../data/searchindex.json";

const PyObject: React.FunctionComponent<{
  module: string;
  object: string;
  displayText?: string;
}> = ({ module, object, displayText }) => {
  const objects = data.objects as any;
  const moduleObjects = objects[module];
  const objectData = moduleObjects[object];
  const fileIndex = objectData[0];
  // TODO: Make sure to use the hashOverride when it's defined
  // const hashOverride = objectData[3];
  const doc = data.docnames[fileIndex];
  const link = doc.replace("sections/api/apidocs/", "/docs/apidocs/");
  return (
    <Link href={link + "#" + module + "." + object}>
      <a>
        <code>{displayText || object}</code>
      </a>
    </Link>
  );
};

export default PyObject;

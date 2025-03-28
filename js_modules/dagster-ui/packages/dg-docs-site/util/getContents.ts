import {ComponentType, Contents, Package} from '@dagster-io/dg-docs-components/types';
import {promises as fs} from 'fs';
import path from 'path';
import process from 'process';

let contents: Contents | null = null;

export default async function getContents(): Promise<Contents | null> {
  if (contents) {
    return contents;
  }

  const jsonPath = path.join(process.cwd(), 'contents', 'generated.json');
  const json = await fs.readFile(jsonPath, 'utf8');

  try {
    contents = JSON.parse(json);
  } catch (error) {
    console.error(error);
  }

  return contents;
}

export async function getPackage(contents: Contents, packageName: string): Promise<Package | null> {
  return contents?.find((pkg) => pkg.name === packageName) ?? null;
}

export async function getComponent(
  contents: Contents,
  packageName: string,
  componentName: string,
): Promise<ComponentType | null> {
  return (
    contents
      ?.find((pkg) => pkg.name === packageName)
      ?.componentTypes.find((component) => component.name === componentName) ?? null
  );
}

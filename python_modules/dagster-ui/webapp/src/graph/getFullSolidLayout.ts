export type IFullPipelineLayout = {
  [solidName: string]: IFullSolidLayout;
};

export interface IFullSolidLayout {
  solid: ILayout;
  inputs: {
    [inputName: string]: {
      layout: ILayout;
      port: IPoint;
    };
  };
  output: {
    layout: ILayout;
    port: IPoint;
  };
}

export interface ILayoutPipeline {
  solids: Array<{
    name: string;
    inputs: Array<{
      name: string;
    }>;
  }>;
}

export interface ILayout {
  x: number;
  y: number;
  height: number;
  width: number;
}

export interface IPoint {
  x: number;
  y: number;
}

const PADDING_LEFT = 100;
const PADDING_TOP = 250;
const SOLID_WIDTH = 250;
const SOLID_BASE_HEIGHT = 60;
const SOLID_GAP = 100;
const INPUT_WIDTH = 200;
const INPUT_HEIGHT = 80;
const INPUT_GAP = 20;
const OUTPUT_WIDTH = 200;
const OUTPUT_HEIGHT = 80;
const INPUT_OUTPUT_INSET = 10;
const SOLID_STEP =
  SOLID_WIDTH + INPUT_WIDTH + OUTPUT_WIDTH - INPUT_OUTPUT_INSET * 2 + SOLID_GAP;

export function getFullPipelineLayout(
  pipeline: ILayoutPipeline
): IFullPipelineLayout {
  const result: IFullPipelineLayout = {};
  pipeline.solids.forEach(({ name }) => {
    result[name] = getFullSolidLayout(pipeline, name);
  });
  return result;
}

export function getFullSolidLayout(
  pipeline: ILayoutPipeline,
  solidName: string
): IFullSolidLayout {
  const solidIndex = pipeline.solids.findIndex(
    ({ name }) => name === solidName
  );
  if (solidIndex !== -1) {
    const solid = pipeline.solids[solidIndex];
    const solidY = PADDING_TOP;
    const solidX = PADDING_LEFT + INPUT_WIDTH + solidIndex * SOLID_STEP;
    const solidLayout: ILayout = {
      x: solidX,
      y: solidY,
      width: SOLID_WIDTH,
      height:
        SOLID_BASE_HEIGHT + (INPUT_HEIGHT + INPUT_GAP) * solid.inputs.length
    };
    const outputX = solidX + SOLID_WIDTH - INPUT_OUTPUT_INSET;
    const outputY = solidY + INPUT_GAP;
    const outputLayout: ILayout = {
      x: outputX,
      y: outputY,
      width: OUTPUT_WIDTH,
      height: OUTPUT_HEIGHT
    };
    const outputPort: IPoint = {
      x: outputX + OUTPUT_WIDTH,
      y: outputY + OUTPUT_HEIGHT / 2
    };
    const inputs: {
      [inputName: string]: {
        layout: ILayout;
        port: IPoint;
      };
    } = {};
    solid.inputs.forEach((input, i) => {
      const inputX = solidX + INPUT_OUTPUT_INSET - INPUT_WIDTH;
      const inputY = solidY + INPUT_GAP + (INPUT_HEIGHT + INPUT_GAP) * i;
      inputs[input.name] = {
        layout: {
          x: inputX,
          y: inputY,
          width: INPUT_WIDTH,
          height: INPUT_HEIGHT
        },
        port: {
          x: inputX,
          y: inputY + INPUT_HEIGHT / 2
        }
      };
    });

    return {
      solid: solidLayout,
      inputs,
      output: {
        layout: outputLayout,
        port: outputPort
      }
    };
  } else {
    throw new Error("Unknown solid");
  }
}

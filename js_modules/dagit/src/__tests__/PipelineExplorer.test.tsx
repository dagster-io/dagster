import { createAdjacencyMatrix } from "../PipelineExplorer";

it("should return a proper adjacency matrix for the single pipeline", () => {
  const mockPipeline = [
    {
      name: "one",
      inputs: [
        {
          dependsOn: []
        }
      ]
    },
    {
      name: "two",
      inputs: [
        {
          dependsOn: [{ solid: { name: "one" } }]
        }
      ]
    }
  ];

  const expectedAdjacencyMatrix = [[0, 0], [1, 0]];

  // expect(createAdjacencyMatrix(mockPipeline)).toBe(expectedAdjacencyMatrix);
});

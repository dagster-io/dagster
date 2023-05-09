import {GanttChartMode} from '../GanttChart';
import {buildLayout} from '../GanttChartLayout';

describe('toGraphQueryItems', () => {
  it('ignores self-dependencies caused by TimeWindowPartitionMapping', () => {
    const result = buildLayout({
      mode: GanttChartMode.FLAT,
      nodes: [
        {
          name: 'depends_on_nothing',
          inputs: [],
          outputs: [{dependedBy: [{solid: {name: 'depends_on_yesterday'}}]}],
        },
        {
          name: 'depends_on_yesterday',
          inputs: [
            {dependsOn: [{solid: {name: 'depends_on_nothing'}}]},
            {dependsOn: [{solid: {name: 'depends_on_yesterday'}}]},
          ],
          outputs: [{dependedBy: [{solid: {name: 'depends_on_yesterday'}}]}],
        },
      ],
    });

    expect(result.markers).toEqual([]);
    expect(result.boxes.length).toEqual(2);
    expect(result.boxes[0]).toMatchObject({
      key: 'depends_on_nothing',
      root: true,
      state: undefined,
      width: 100,
      x: 16,
      y: 0,
    });
    expect(result.boxes[0].children.length).toEqual(1);
    expect(result.boxes[1]).toMatchObject({
      key: 'depends_on_yesterday',
      root: false,
      state: undefined,
      width: 100,
      x: 152,
      y: 1,
    });
  });
});

import {humanizeSensorCursor} from '../SensorDetails';

describe('SensorDetails', () => {
  describe('humanizeSensorCursor', () => {
    it('displays populated fields in a minimal format', () => {
      expect(
        humanizeSensorCursor(
          '{"__class__": "AirflowPollingSensorCursor", "dag_query_offset": 0, "end_date_gte": 1743134332.087687, "end_date_lte": null}',
        ),
      ).toEqual('end_date_gte=1743134332.087687');

      expect(
        humanizeSensorCursor(
          '{"__class__": "RunStatusSensorCursor", "record_id": 1234, "update_timestamp": "1743134332", "record_timestamp": null}',
        ),
      ).toEqual('record_id=1234,update_timestamp=1743134332');

      expect(humanizeSensorCursor('1234')).toEqual('1234');
      expect(humanizeSensorCursor(false)).toEqual(false);
      expect(humanizeSensorCursor(null)).toEqual(null);
    });
  });
});

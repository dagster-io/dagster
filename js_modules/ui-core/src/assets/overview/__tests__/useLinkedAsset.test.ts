import {findLinkedAssetResult} from '../useLinkedAsset';

const asset = (path: string[], tableName: string | null, storageKind: string | null = null) => ({
  key: {path},
  definition: tableName ? {storageAddress: {tableName, storageKind}} : null,
});

describe('findLinkedAssetResult', () => {
  const assets = [
    asset(['conn', 'orders'], 'DB.PUBLIC.ORDERS', 'snowflake'),
    asset(['sda', 'orders'], 'db.public.orders', 'snowflake'),
    asset(['sda', 'orders_bq'], 'db.public.orders', 'bigquery'),
    asset(['sda', 'users'], 'db.public.users', null),
    asset(['sda', 'events_a'], 'db.public.events', null),
    asset(['sda', 'events_b'], 'db.public.events', null),
    asset(['sda', 'no_storage'], null),
  ];

  it('prefers a single table + storage kind match, ignoring case and the asset itself', () => {
    expect(
      findLinkedAssetResult(
        {path: ['conn', 'orders']},
        {tableName: 'DB.PUBLIC.ORDERS', storageKind: 'Snowflake'},
        assets,
      ),
    ).toEqual({type: 'linked', linkedAssetKey: {path: ['sda', 'orders']}});
  });

  it('falls back to a single table-only match', () => {
    expect(
      findLinkedAssetResult(
        {path: ['conn', 'users']},
        {tableName: 'db.public.users', storageKind: 'snowflake'},
        assets,
      ),
    ).toEqual({type: 'linked', linkedAssetKey: {path: ['sda', 'users']}});
  });

  it('is ambiguous when several tables match and no storage kind narrows it', () => {
    expect(
      findLinkedAssetResult(
        {path: ['conn', 'events']},
        {tableName: 'db.public.events', storageKind: null},
        assets,
      ),
    ).toEqual({type: 'ambiguous'});
  });

  it('returns none without a table name or a match', () => {
    expect(findLinkedAssetResult({path: ['x']}, null, assets)).toEqual({type: 'none'});
    expect(
      findLinkedAssetResult(
        {path: ['x']},
        {tableName: 'db.public.missing', storageKind: null},
        assets,
      ),
    ).toEqual({type: 'none'});
  });
});

import {NonIdealState} from '@dagster-io/ui-components';

export const AssetsEmptyState = ({prefixPath}: {prefixPath?: string[]}) => (
  <NonIdealState
    icon="asset"
    title="资产"
    description={
      <p>
        {prefixPath && prefixPath.length
          ? `没有匹配指定资产键的已物化资产。`
          : `暂无已知的已物化资产。`}
        任何在流水线运行期间通过 <code>AssetMaterialization</code> 指定的资产键都会显示在这里。
        详情请参阅{' '}
        <a href="https://docs.dagster.io/_apidocs/ops#dagster.AssetMaterialization">
          AssetMaterialization 文档
        </a>
        。
      </p>
    }
  />
);

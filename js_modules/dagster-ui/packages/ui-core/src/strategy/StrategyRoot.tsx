/**
 * StrategyRoot - 策略配置页面
 * 嵌入 Profile Editor 微前端
 */
import {Box, Colors, Heading, NonIdealState, PageHeader, Spinner} from '@dagster-io/ui-components';
import {memo, useState, useCallback, useMemo} from 'react';

// Profile Editor 端口
const PROFILE_EDITOR_PORT = process.env.REACT_APP_PROFILE_EDITOR_PORT || '3001';

/**
 * 动态获取 Profile Editor URL
 * 使用当前页面的 hostname，确保用户通过任何 IP 访问都能正常工作
 */
function getProfileEditorUrl(): string {
  // 优先使用环境变量配置的完整 URL
  if (process.env.REACT_APP_PROFILE_EDITOR_URL) {
    return process.env.REACT_APP_PROFILE_EDITOR_URL;
  }
  // 否则使用当前 hostname + 端口
  const {protocol, hostname} = window.location;
  return `${protocol}//${hostname}:${PROFILE_EDITOR_PORT}`;
}

export const StrategyRoot = memo(() => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 动态计算 Profile Editor URL，基于当前 hostname
  const profileEditorUrl = useMemo(() => getProfileEditorUrl(), []);

  const handleIframeLoad = useCallback(() => {
    setLoading(false);
  }, []);

  const handleIframeError = useCallback(() => {
    setLoading(false);
    setError('无法加载策略配置编辑器。请确保 Profile Editor 服务正在运行。');
  }, []);

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%'}}>
      <PageHeader
        title={<Heading>策略配置</Heading>}
      />
      <Box
        flex={{direction: 'column', grow: 1}}
        style={{
          position: 'relative',
          background: Colors.backgroundDefault(),
          overflow: 'hidden',
        }}
      >
        {loading && (
          <Box
            flex={{direction: 'column', alignItems: 'center', justifyContent: 'center'}}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: Colors.backgroundDefault(),
              zIndex: 10,
            }}
          >
            <Spinner purpose="page" />
            <Box margin={{top: 16}}>正在加载策略配置编辑器...</Box>
          </Box>
        )}
        {error ? (
          <NonIdealState
            icon="error"
            title="加载失败"
            description={error}
            action={
              <Box flex={{direction: 'column', gap: 8, alignItems: 'center'}}>
                <Box>请确保 Profile Editor 服务正在运行:</Box>
                <Box
                  style={{
                    fontFamily: 'monospace',
                    background: Colors.backgroundLight(),
                    padding: '8px 12px',
                    borderRadius: 4,
                  }}
                >
                  cd dsl-editor/frontend && npm run dev
                </Box>
              </Box>
            }
          />
        ) : (
          <iframe
            src={`${profileEditorUrl}?mode=profile`}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              display: loading ? 'none' : 'block',
            }}
            onLoad={handleIframeLoad}
            onError={handleIframeError}
            title="策略配置编辑器"
            allow="clipboard-read; clipboard-write"
          />
        )}
      </Box>
    </Box>
  );
});

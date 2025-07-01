"""Tests for dagster_webserver.json utilities."""

import json

import pytest
from dagster_webserver.json import OptimizedJSONResponse, _is_browser_request, create_json_response
from starlette.responses import JSONResponse


class MockRequest:
    """Mock request object for testing."""

    def __init__(self, user_agent: str = ""):
        self.headers = {"user-agent": user_agent}


class TestBrowserDetection:
    """Test browser detection functionality."""

    def test_browser_user_agents_detected(self):
        """Test that common browser user agents are detected as browsers."""
        browser_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.90",
        ]

        for agent in browser_agents:
            request = MockRequest(agent)
            assert _is_browser_request(request), f"Should detect browser: {agent[:50]}..."

    def test_non_browser_user_agents_not_detected(self):
        """Test that non-browser user agents are not detected as browsers."""
        non_browser_agents = [
            "curl/7.68.0",
            "python-requests/2.25.1",
            "PostmanRuntime/7.28.0",
            "httpie/2.4.0",
            "Wget/1.20.3 (linux-gnu)",
            "Apache-HttpClient/4.5.13 (Java/11.0.11)",
            "Go-http-client/1.1",
            "",  # Empty user agent
        ]

        for agent in non_browser_agents:
            request = MockRequest(agent)
            assert not _is_browser_request(request), f"Should not detect browser: {agent}"

    def test_case_insensitive_detection(self):
        """Test that browser detection is case-insensitive."""
        mixed_case_agents = [
            "MOZILLA/5.0 (Chrome/91.0) Safari/537.36",
            "mozilla/5.0 (firefox/89.0)",
            "Chrome/91.0.4472.124",
            "SAFARI/14.1.1",
        ]

        for agent in mixed_case_agents:
            request = MockRequest(agent)
            assert _is_browser_request(request), (
                f"Should detect browser (case-insensitive): {agent}"
            )

    def test_partial_browser_indicators(self):
        """Test that partial browser indicators work correctly."""
        partial_agents = [
            "CustomBrowser/1.0",
            "MyApp/1.0 (mozilla-compatible)",
            "Tool/1.0 contains-chrome-string",
            "App/1.0 with-safari-in-name",
        ]

        for agent in partial_agents:
            request = MockRequest(agent)
            assert _is_browser_request(request), f"Should detect browser indicator: {agent}"


class TestOptimizedJSONResponse:
    """Test OptimizedJSONResponse functionality."""

    def test_initialization(self):
        """Test OptimizedJSONResponse initialization."""
        content = {"key": "value"}
        response = OptimizedJSONResponse(content)

        assert response.status_code == 200
        assert response.media_type == "application/json"

    def test_initialization_with_custom_status(self):
        """Test OptimizedJSONResponse with custom status code."""
        content = {"error": "Not found"}
        response = OptimizedJSONResponse(content, status_code=404)

        assert response.status_code == 404
        assert response.media_type == "application/json"

    def test_initialization_with_headers(self):
        """Test OptimizedJSONResponse with custom headers."""
        content = {"data": "test"}
        headers = {"X-Custom-Header": "test-value"}
        response = OptimizedJSONResponse(content, headers=headers)

        assert response.headers["X-Custom-Header"] == "test-value"

    def test_render_simple_data(self):
        """Test rendering simple JSON data."""
        content = {"message": "hello", "number": 42, "boolean": True}
        response = OptimizedJSONResponse(content)

        rendered = response.render(content)
        assert isinstance(rendered, bytes)

        # Parse back to verify correctness
        parsed = json.loads(rendered.decode())
        assert parsed == content

    def test_render_complex_data(self):
        """Test rendering complex JSON data structures."""
        content = {
            "nested": {
                "array": [1, 2, 3, {"inner": "value"}],
                "null_value": None,
                "float": 3.14159,
            },
            "list": ["a", "b", "c"],
            "empty_dict": {},
            "empty_list": [],
        }
        response = OptimizedJSONResponse(content)

        rendered = response.render(content)
        parsed = json.loads(rendered.decode())
        assert parsed == content

    def test_render_numpy_data(self):
        """Test rendering data with numpy arrays (if available)."""
        try:
            import numpy as np

            content = {"numpy_array": np.array([1, 2, 3]).tolist()}
            response = OptimizedJSONResponse(content)

            rendered = response.render(content)
            parsed = json.loads(rendered.decode())
            assert parsed == content
        except ImportError:
            # Skip test if numpy is not available
            pytest.skip("numpy not available")


class TestCreateJSONResponse:
    """Test create_json_response factory function."""

    def test_browser_request_returns_optimized_response(self):
        """Test that browser requests get OptimizedJSONResponse."""
        browser_request = MockRequest("Mozilla/5.0 (Chrome/91.0) Safari/537.36")
        content = {"message": "test"}

        response = create_json_response(content, browser_request)
        assert isinstance(response, OptimizedJSONResponse)
        assert response.status_code == 200

    def test_non_browser_request_returns_json_response(self):
        """Test that non-browser requests get JSONResponse."""
        api_request = MockRequest("python-requests/2.25.1")
        content = {"message": "test"}

        response = create_json_response(content, api_request)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

    def test_custom_status_code(self):
        """Test create_json_response with custom status code."""
        browser_request = MockRequest("Mozilla/5.0 (Chrome/91.0)")
        api_request = MockRequest("curl/7.68.0")
        content = {"error": "Not found"}

        browser_response = create_json_response(content, browser_request, status_code=404)
        api_response = create_json_response(content, api_request, status_code=404)

        assert isinstance(browser_response, OptimizedJSONResponse)
        assert browser_response.status_code == 404
        assert isinstance(api_response, JSONResponse)
        assert api_response.status_code == 404

    def test_custom_headers(self):
        """Test create_json_response with custom headers."""
        browser_request = MockRequest("Mozilla/5.0 (Safari/14.1)")
        content = {"data": "test"}
        headers = {"X-Test-Header": "test-value"}

        response = create_json_response(content, browser_request, headers=headers)
        assert isinstance(response, OptimizedJSONResponse)
        assert response.headers["X-Test-Header"] == "test-value"

    def test_empty_content(self):
        """Test create_json_response with empty content."""
        browser_request = MockRequest("Mozilla/5.0 (Firefox/89.0)")
        api_request = MockRequest("httpie/2.4.0")

        browser_response = create_json_response({}, browser_request)
        api_response = create_json_response({}, api_request)

        assert isinstance(browser_response, OptimizedJSONResponse)
        assert isinstance(api_response, JSONResponse)

    def test_large_content(self):
        """Test create_json_response with large content."""
        large_content = {"data": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}

        browser_request = MockRequest("Mozilla/5.0 (Edge/91.0)")
        api_request = MockRequest("wget/1.20.3")

        browser_response = create_json_response(large_content, browser_request)
        api_response = create_json_response(large_content, api_request)

        assert isinstance(browser_response, OptimizedJSONResponse)
        assert isinstance(api_response, JSONResponse)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_missing_user_agent_header(self):
        """Test behavior when user-agent header is missing."""

        class MockRequestNoUserAgent:
            def __init__(self):
                self.headers = {}

        request = MockRequestNoUserAgent()
        assert not _is_browser_request(request)

        response = create_json_response({"test": "data"}, request)
        assert isinstance(response, JSONResponse)

    def test_none_user_agent(self):
        """Test behavior when user-agent is None."""

        class MockRequestNoneUserAgent:
            def __init__(self):
                self.headers = {"user-agent": None}

        request = MockRequestNoneUserAgent()
        # This should handle None gracefully and not detect as browser
        response = create_json_response({"test": "data"}, request)
        assert isinstance(response, JSONResponse)

    def test_unicode_content(self):
        """Test handling of unicode content."""
        content = {
            "unicode_text": "Hello 世界 🌍",
            "emoji": "🚀🎉💫",
            "accents": "café naïve résumé",
        }

        browser_request = MockRequest("Mozilla/5.0 (Chrome/91.0)")
        response = create_json_response(content, browser_request)

        assert isinstance(response, OptimizedJSONResponse)
        rendered = response.render(content)
        parsed = json.loads(rendered.decode())
        assert parsed == content


class TestPerformanceConsiderations:
    """Test performance-related aspects."""

    def test_orjson_vs_json_consistency(self):
        """Test that orjson and json produce equivalent results."""
        test_data = {
            "string": "test",
            "number": 42,
            "float": 3.14159,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"},
        }

        # Create responses
        browser_request = MockRequest("Mozilla/5.0 (Chrome/91.0)")
        api_request = MockRequest("curl/7.68.0")

        optimized_response = create_json_response(test_data, browser_request)
        standard_response = create_json_response(test_data, api_request)

        # Render both
        optimized_rendered = optimized_response.render(test_data)
        standard_rendered = standard_response.render(test_data)

        # Parse both back
        optimized_parsed = json.loads(optimized_rendered.decode())
        standard_parsed = json.loads(standard_rendered.decode())

        # Should be equivalent
        assert optimized_parsed == standard_parsed == test_data

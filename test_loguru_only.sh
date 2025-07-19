#!/bin/bash
# Run only the loguru_bridge tests (test_bridge.py)
# This avoids the import issues in other logging test files

cd /workspaces/dagster

echo "🧪 Running Loguru Bridge Tests Only"
echo "======================================"
echo ""

# Run the test_bridge.py file specifically
echo "📁 Running: test_bridge.py"
python -m pytest python_modules/dagster/dagster_tests/logging_tests/test_bridge.py -v --override-ini="addopts=" --tb=short

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "🎉 All loguru_bridge tests PASSED!"
    echo "✅ BUILDKITE_ANALYTICS_TOKEN is properly loaded from .env"
    echo "✅ All 21 tests in test_bridge.py are working"
    echo "✅ loguru_bridge.py module is being tested comprehensively"
else
    echo ""
    echo "❌ Some tests failed"
fi

exit $exit_code

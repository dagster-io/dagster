"""Test suite for sphinx-mdx-builder."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace


class TestMdxBuilder:
    """Test class for the MDX builder functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def test_docs_dir(self):
        """Get the path to the test documentation directory."""
        return Path(__file__).parent / "test_docs"

    @pytest.fixture
    def built_docs(self, temp_dir, test_docs_dir):
        """Build the test documentation using the MDX builder."""
        srcdir = str(test_docs_dir)
        outdir = os.path.join(temp_dir, "_build", "mdx")
        doctreedir = os.path.join(temp_dir, "_build", "doctrees")
        confdir = str(test_docs_dir)

        # Add the dummy module to the Python path
        import sys

        dummy_module_path = str(Path(__file__).parent)
        if dummy_module_path not in sys.path:
            sys.path.insert(0, dummy_module_path)

        with docutils_namespace():
            app = Sphinx(
                srcdir=srcdir,
                confdir=confdir,
                outdir=outdir,
                doctreedir=doctreedir,
                buildername="mdx",
            )
            app.build()

        return Path(outdir)

    def test_mdx_files_generated(self, built_docs):
        """Test that MDX files are generated."""
        # Check that the output directory exists
        assert built_docs.exists(), f"Output directory {built_docs} does not exist"

        # Check that index.mdx is generated
        index_file = built_docs / "index.mdx"
        assert index_file.exists(), "index.mdx file was not generated"

        # Check that dummy_module.mdx is generated
        dummy_module_file = built_docs / "dummy_module.mdx"
        assert dummy_module_file.exists(), "dummy_module.mdx file was not generated"

    def test_index_mdx_content(self, built_docs):
        """Test the content of the generated index.mdx file."""
        index_file = built_docs / "index.mdx"
        content = index_file.read_text()

        # Check for frontmatter
        assert content.startswith("---"), "MDX file should start with frontmatter"
        assert "title:" in content, "Frontmatter should contain title"
        assert "description:" in content, "Frontmatter should contain description"

        # Check for main content
        assert "Test Documentation" in content, "Should contain main heading"
        assert "Welcome to the test documentation" in content, "Should contain intro text"
        assert "sphinx-mdx-builder" in content, "Should mention the builder"

    def test_dummy_module_mdx_content(self, built_docs):
        """Test the content of the generated dummy_module.mdx file."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        # Check for frontmatter
        assert content.startswith("---"), "MDX file should start with frontmatter"
        assert "title:" in content, "Frontmatter should contain title"

        # Check for module documentation
        assert "Dummy Module Documentation" in content, "Should contain module heading"
        assert "Vehicle" in content, "Should document Vehicle class"
        assert "Car" in content, "Should document Car class"
        assert "Color" in content, "Should document Color enum"

        # Check for function documentation
        assert "calculate_fuel_efficiency" in content, (
            "Should document calculate_fuel_efficiency function"
        )
        assert "find_cars_by_color" in content, "Should document find_cars_by_color function"
        assert "get_car_summary" in content, "Should document get_car_summary function"

        # Check for constants section
        assert "Constants" in content, "Should have Constants section"
        assert "DEFAULT_CAR_COLOR" in content, "Should mention DEFAULT_CAR_COLOR"
        assert "MAX_VEHICLE_AGE" in content, "Should mention MAX_VEHICLE_AGE"

    def test_mdx_frontmatter_structure(self, built_docs):
        """Test that the MDX frontmatter has the correct structure."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        lines = content.split("\n")

        # Find frontmatter boundaries
        frontmatter_start = None
        frontmatter_end = None

        for i, line in enumerate(lines):
            if line.strip() == "---":
                if frontmatter_start is None:
                    frontmatter_start = i
                else:
                    frontmatter_end = i
                    break

        assert frontmatter_start is not None, "Should have frontmatter start"
        assert frontmatter_end is not None, "Should have frontmatter end"

        frontmatter_lines = lines[frontmatter_start + 1 : frontmatter_end]
        frontmatter_content = "\n".join(frontmatter_lines)

        # Check for expected frontmatter fields
        assert "title:" in frontmatter_content, "Should have title field"
        assert "| Test Docs" in frontmatter_content, "Should have title suffix from config"

    def test_class_documentation_structure(self, built_docs):
        """Test that class documentation is properly structured."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        # Check for class hierarchy (Car extends Vehicle)
        assert "Vehicle" in content, "Should document base Vehicle class"
        assert "Car" in content, "Should document Car class"

        # Check for method documentation
        assert "start_engine" in content, "Should document Vehicle.start_engine method"
        assert "honk_horn" in content, "Should document Car.honk_horn method"

        # Check for parameter documentation (MDX builder uses "Parameters:" instead of "Args:")
        assert "Parameters:" in content, "Should have Parameters sections"
        assert "Returns:" in content, "Should have Returns sections"

    def test_function_documentation_structure(self, built_docs):
        """Test that function documentation is properly structured."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        # Check for function signatures and documentation
        assert "calculate_fuel_efficiency" in content, "Should document function"
        assert "distance" in content, "Should show parameter names"
        assert "fuel_used" in content, "Should show parameter names"
        assert "ValueError" in content, "Should document exceptions"

    def test_enum_documentation(self, built_docs):
        """Test that enum documentation is included."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        # Check for enum documentation
        assert "Color" in content, "Should document Color enum"
        assert "RED" in content or "red" in content, "Should document enum values"
        assert "GREEN" in content or "green" in content, "Should document enum values"
        assert "BLUE" in content or "blue" in content, "Should document enum values"

    def test_configuration_options_applied(self, built_docs):
        """Test that configuration options are properly applied."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        # Check that title suffix is applied (from conf.py: mdx_title_suffix = ' | Test Docs')
        assert "| Test Docs" in content, "Should apply title suffix from configuration"

        # Check file extension is .mdx
        assert dummy_module_file.suffix == ".mdx", "Should generate .mdx files"

        # Check that GitHub URL configuration is applied (if source links are present)
        if "github.com" in content:
            assert "test-repo" in content, "Should use configured GitHub URL"

    def test_source_links_generation(self, built_docs):
        """Test that [source] links are properly generated."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        # Check for source links presence
        assert "[source]" in content, "Should contain [source] links"
        assert "className='source-link'" in content, "Should have proper source link styling"

        # Check for GitHub URLs in source links
        assert "https://github.com/test/test-repo/blob/main" in content, (
            "Should use configured GitHub base URL"
        )

        # Check for specific source file references
        assert "tests/dummy_module.py" in content, "Should reference the dummy module source file"

        # Check for line number references (source links should include line numbers)
        import re

        line_number_pattern = r"tests/dummy_module\.py#L\d+"
        assert re.search(line_number_pattern, content), "Source links should include line numbers"

        # Check that source links are properly formatted as JSX components
        assert "target='_blank'" in content, "Source links should open in new tab"
        assert "rel='noopener noreferrer'" in content, (
            "Source links should have proper security attributes"
        )

    def test_decorated_function_source_links(self, built_docs):
        """Test that decorated functions have source links generated properly."""
        dummy_module_file = built_docs / "dummy_module.mdx"
        content = dummy_module_file.read_text()

        # Test functions with different wrapper patterns
        wrapper_functions = [
            ("test_dagster_style_logger", 202, 208),  # Custom wrapper with logger_fn
            ("test_func_wrapper", 224, 230),  # GenericWrapper with func
            ("test_function_wrapper", 234, 240),  # GenericWrapper with function
            ("test_callback_wrapper", 243, 249),  # GenericWrapper with callback
        ]

        # Check that source links are present
        assert "[source]" in content, "Should have source links for wrapped functions"

        import re

        # Find all source links in the content
        source_link_pattern = (
            r"<a[^>]*href='([^']*tests/dummy_module\.py#L\d+)'[^>]*>\[source\]</a>"
        )
        source_links = re.findall(source_link_pattern, content)

        # Check that we have source links
        assert len(source_links) > 0, "Should have at least one source link for functions"

        # Check each wrapper function has its source link
        found_functions = []
        for func_name, start_line, end_line in wrapper_functions:
            # Check that the function is documented
            if func_name in content:
                found_functions.append(func_name)

                # Look for source link in the expected line range
                function_source_found = False
                for link in source_links:
                    if "dummy_module.py#L" in link:
                        line_match = re.search(r"#L(\d+)", link)
                        if line_match:
                            line_num = int(line_match.group(1))
                            if start_line <= line_num <= end_line:
                                function_source_found = True
                                break

                assert function_source_found, (
                    f"Should have source link for wrapped function {func_name} "
                    f"in line range {start_line}-{end_line}. "
                    f"Found source links: {source_links}"
                )

        # Ensure we found at least some of the wrapper functions
        assert len(found_functions) >= 2, (
            f"Should document multiple wrapper functions. Found: {found_functions}"
        )


def test_direct_builder_import():
    """Test that the builder can be imported directly."""
    from sphinxcontrib.mdxbuilder.builders.mdx import MdxBuilder

    assert MdxBuilder.name == "mdx", "Builder should have correct name"
    assert MdxBuilder.format == "mdx", "Builder should have correct format"

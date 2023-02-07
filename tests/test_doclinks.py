"""Unit tests for checking database model for links to external documentation."""

import pytest

from matl_online.public.models import DocumentationLink

from .factories import DocumentationLinkFactory as DocLink


@pytest.mark.usefixtures("db")
class TestDocumentationLink:
    """Series of tests for the DocumentationLink database model."""

    def test_refresh_single(self, mocker, testapp):
        """Handle parsing a single doc entry."""
        req = mocker.patch("matl_online.matl.requests.get")
        testapp.app.config["MATLAB_DOC_LINKS"] = ["https://mathworks.com"]

        function_name = "func"
        function_link = "http://link.html"

        req.return_value.text = _create_html([(function_name, function_link)])

        out = DocumentationLink.refresh()
        assert len(out) == 1

        link = out[0]

        assert link.name == function_name
        assert link.link == function_link
        assert req.call_count == 1

    def test_refresh_multiple(self, mocker, testapp):
        """Parse out multiple functions at the same time."""
        req = mocker.patch("matl_online.matl.requests.get")
        testapp.app.config["MATLAB_DOC_LINKS"] = ["https://mathworks.com"]

        funcs = [
            ("func1", "https://func1.html"),
            ("func2", "https://func2.html"),
            ("func3", "https://func3.html"),
        ]

        req.return_value.text = _create_html(funcs)
        out = DocumentationLink.refresh()

        assert len(out) == len(funcs)

        names = [item.name for item in out]
        links = [item.link for item in out]

        for name, link in funcs:
            assert name in names and link in links

    def test_refresh_duplicates(self, mocker, testapp):
        """Handle two entries for the same function."""
        req = mocker.patch("matl_online.matl.requests.get")
        testapp.app.config["MATLAB_DOC_LINKS"] = ["https://mathworks.com"]

        funcs = [
            ("func1", "https://func1.html"),
            ("func2", "https://func2.html"),
            ("func3", "https://func3.html"),
            ("func3", "https://func3.html"),
        ]

        req.return_value.text = _create_html(funcs)
        out = DocumentationLink.refresh()

        assert len(out) == len(funcs) - 1

        names = [item.name for item in out]
        links = [item.link for item in out]

        for name, link in funcs:
            assert name in names and link in links

    def test_remove_ij(self, mocker, testapp):
        """Variables i and j should be removed by default if they are present."""
        req = mocker.patch("matl_online.matl.requests.get")
        testapp.app.config["MATLAB_DOC_LINKS"] = ["https://mathworks.com"]

        # Go ahead and add i and j entries
        DocLink(name="i")
        DocLink(name="j")

        # Ensure that they are actually there
        assert DocumentationLink.query.filter_by(name="i").count() == 1
        assert DocumentationLink.query.filter_by(name="j").count() == 1

        # Now pass a single function in
        function_name = "func"
        function_link = "http://link.html"

        req.return_value.text = _create_html([(function_name, function_link)])

        out = DocumentationLink.refresh()

        # Make sure that i and j were automatically removed
        assert len(out) == 1

        assert DocumentationLink.query.filter_by(name="i").count() == 0
        assert DocumentationLink.query.filter_by(name="j").count() == 0


def _create_html(data):
    """Create fake HTML for the mock object to return."""
    out = "<table>"
    template = '<tr><td class="term"><a href="%s">%s</a></td></tr>'

    for func, link in data:
        out = out + template % (link, func)

    return out + "</table>"

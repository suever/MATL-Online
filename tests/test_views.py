"""Tests for checking user interaction with views."""

import json
import operator
import pathlib

from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from pytest_mock.plugin import MockerFixture
from webtest import TestApp  # type: ignore

from matl_online.public.models import Release

from .factories import ReleaseFactory


class TestShare:
    """Tests the /share route for uploading to imgur."""

    def test_share_with_csrf(
        self,
        app: Flask,
        testapp: TestApp,
        mocker: MockerFixture,
    ) -> None:
        """Passing CSRF validation check."""
        csrf = mocker.patch("matl_online.public.views.validate_csrf")
        csrf.return_value = True

        post = mocker.patch("matl_online.public.views.requests.post")
        data = {
            "success": True,
            "data": {"link": "https://link"},
        }
        post.return_value.text = json.dumps(data)

        url = url_for("public.share", data="base64,data")

        response = testapp.post(url)

        # Make sure that CSRF token was actually checked
        assert csrf.call_count == 1
        assert post.call_count == 1

        head_expect = {"Authorization": "Client-ID " + app.config["IMGUR_CLIENT_ID"]}

        post.assert_called_once_with(
            "https://api.imgur.com/3/image",
            {"image": "data", "type": "base64"},
            headers=head_expect,
        )

        # Make sure that the response was correct
        assert response.status_code == 200

        payload = response.json

        assert payload.get("success") is True
        assert isinstance(data["data"], dict)
        assert payload.get("link") == data["data"]["link"]

    def test_share_with_invalid_csrf(self, testapp: TestApp) -> None:
        """Failing CSRF validation produces an error."""
        url = url_for("public.share", data="INVALID")
        resp = testapp.post_json(url, "", expect_errors=True)
        assert resp.status_code == 400

    def test_share_without_csrf(self, testapp: TestApp) -> None:
        """Failing CSRF validation produces an error."""
        url = url_for("public.share", data="")
        resp = testapp.post_json(url, "", expect_errors=True)
        assert resp.status_code == 400

    def test_failed_upload(self, testapp: TestApp, mocker: MockerFixture) -> None:
        """Test if there was an error while uploading to imgur."""
        csrf = mocker.patch("matl_online.public.views.validate_csrf")
        csrf.return_value = True

        post = mocker.patch("matl_online.public.views.requests.post")
        post.return_value.text = json.dumps({"success": False})

        url = url_for("public.share", data="data")

        response = testapp.post(url, expect_errors=True)

        assert csrf.call_count == 1
        assert post.call_count == 1

        assert response.status_code == 400
        assert response.json.get("success") is False


class TestHome:
    """Test the main page of the site."""

    def test_defaults(
        self,
        testapp: TestApp,
        mocker: MockerFixture,
        db: SQLAlchemy,
    ) -> None:
        """Check the default arguments passed to template."""
        url = url_for("public.home")
        ReleaseFactory.create_batch(size=10)  # type: ignore[attr-defined]

        render = mocker.patch("matl_online.public.views.render_template")
        render.return_value = ""

        testapp.get(url)

        args, params = render.call_args

        assert args[0] == "index.html"
        assert params.get("inputs") == ""
        assert params.get("code") == ""

        latest_release = Release.latest()

        assert latest_release
        assert params.get("version") == latest_release.tag

        versions = params.get("versions")
        versions = sorted(versions, key=operator.attrgetter("tag"))

        releases = Release.query.all()
        releases = sorted(releases, key=operator.attrgetter("tag"))

        assert versions == releases

    def test_non_existent_version(
        self,
        testapp: TestApp,
        mocker: MockerFixture,
        db: SQLAlchemy,
    ) -> None:
        """Pass an invalid version number via query string."""
        url = url_for("public.home", version="not a version")
        ReleaseFactory.create_batch(size=10)  # type: ignore[attr-defined]

        render = mocker.patch("matl_online.public.views.render_template")
        render.return_value = ""

        testapp.get(url)

        version = render.call_args[1].get("version")

        latest_release = Release.latest()

        assert latest_release
        assert version == latest_release.tag


class TestPrivacy:
    """Test privacy policy and associated routes."""

    def test_privacy_page(self, testapp: TestApp) -> None:
        """Test the main view for errors."""
        url = url_for("public.privacy")
        resp = testapp.get(url)
        assert resp.status_code == 200

    def test_api(self, testapp: TestApp) -> None:
        """Test the API for toggling the opt-in/opt-out status."""
        url = url_for("public.privacy_opt")

        opts = [
            ("true", "true"),
            ("true", "false"),
            ("false", "false"),
            ("false", "true"),
        ]

        for previous, current in opts:
            testapp.set_cookie("gaoptout", previous)
            resp = testapp.get(url, params={"value": current})

            assert resp.status_code == 200
            assert resp.json["previous"] == previous
            assert resp.json["current"] == current
            assert testapp.cookies["gaoptout"] == current

    def test_opt_out(self, testapp: TestApp) -> None:
        """Make sure that the cookie is respected."""
        url = url_for("public.privacy")

        # Opt-In
        testapp.set_cookie("gaoptout", "false")
        resp = testapp.get(url)

        assert resp.status_code == 200
        assert resp.text.find("GoogleAnalyticsObject") != -1

        # Opt-Out
        testapp.set_cookie("gaoptout", "true")
        resp = testapp.get(url)

        assert resp.status_code == 200
        assert resp.text.find("GoogleAnalyticsObject") == -1


class TestExplain:
    """Test the /explain route."""

    def test_with_version(
        self,
        testapp: TestApp,
        mocker: MockerFixture,
        db: SQLAlchemy,
    ) -> None:
        """Specify a version and get a successful response."""
        ReleaseFactory.build(tag="1.2.3")
        ReleaseFactory.build(tag="2.4.5")

        version = "1.2.3"
        url = url_for("public.explain", version=version)

        data = {"data": "this"}

        task = mocker.patch("matl_online.public.views.matl_task.delay")
        task.return_value.wait = lambda: data

        resp = testapp.get(url)

        assert resp.status_code == 200
        assert resp.json == data

    def test_no_version(
        self,
        testapp: TestApp,
        mocker: MockerFixture,
        db: SQLAlchemy,
    ) -> None:
        """Do not specify a version and use the latest version."""
        releases = ReleaseFactory.create_batch(size=3)  # type: ignore[attr-defined]

        task = mocker.patch("matl_online.public.views.matl_task.delay")
        task.return_value.wait = lambda: {}

        resp = testapp.get(url_for("public.explain"))

        assert resp.status_code == 200
        assert task.call_args[0][0].version == releases[-1].tag


def test_fetch_help(
    testapp: TestApp,
    mocker: MockerFixture,
    db: SQLAlchemy,
    tmp_path: pathlib.Path,
) -> None:
    """Check that we get the expected JSON when requesting help."""
    folder = mocker.patch("matl_online.matl.documentation.get_matl_folder")
    folder.return_value = tmp_path

    jsonfile = tmp_path.joinpath("help.json")
    data = {"placeholder": "value"}

    with open(jsonfile, "w") as fid:
        fid.write(json.dumps(data))

    version = "1.2.3"
    ReleaseFactory.create(tag=version)

    url = url_for("public.documentation", version=version)

    resp = testapp.get(url)

    assert resp.status_code == 200
    assert resp.json == data


def test_fetch_help_invalid_version(
    testapp: TestApp,
    mocker: MockerFixture,
    db: SQLAlchemy,
    tmp_path: pathlib.Path,
) -> None:
    """Check that we get an error when we try to fetch help for a non-existent version."""
    folder = mocker.patch("matl_online.matl.documentation.get_matl_folder")
    folder.return_value = tmp_path

    jsonfile = tmp_path.joinpath("help.json")
    data = {"placeholder": "value"}

    with open(jsonfile, "w") as fid:
        fid.write(json.dumps(data))

    url = url_for("public.documentation", version="blah")

    resp = testapp.get(url, expect_errors=True)

    assert resp.status_code == 404

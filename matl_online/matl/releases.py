import shutil

import requests
from dateutil import parser as date_parser
from flask import current_app

from matl_online.public.models import Release

from .source import get_matl_folder


def refresh_releases() -> None:
    """Fetch new release information from GitHub and update local database."""
    repo = current_app.config["MATL_REPO"]
    resp = requests.get("https://api.github.com/repos/%s/releases" % repo)

    for item in resp.json():
        # Skip any pre-releases since they aren't ready for prime-time
        if item["prerelease"]:
            continue

        pubdate = date_parser.parse(item["published_at"])

        # Query the database for this release number
        release = Release.query.filter_by(tag=item["tag_name"]).first()

        if release is None:
            # This is a new release, and we don't need to do much
            Release.create(tag=item["tag_name"], date=pubdate)

        elif release.date != pubdate:
            # We have an updated release, and we need to clean up
            source_dir = get_matl_folder(item["tag_name"], install=False)

            # If we had previously downloaded this code, then delete it
            if source_dir is not None:
                shutil.rmtree(source_dir)

            # Now update the database entry
            release.update(date=pubdate)

"""Module for retrieving and parsing MATL Answers."""

import re

from bs4 import BeautifulSoup
from flask import current_app
from stackexchange import Site, ProgrammingPuzzlesampCodeGolf
from stackexchange.models import Answer as StackExchangeAnswer

from matl_online.utils import grouper
from matl_online.analytics.models import Answer, StackExchangeUser


# An Answer filter to use for the SE API so that we get back specific fields
ANSWER_FILTER = '!b0OfNb3Hk1Ze71'


class MATLAnswer(StackExchangeAnswer):
    """A Class for representing a MATL Answer on PPCG."""

    # This is a default ID to prevent issues when one is not-assigned
    id = 0


def fetch_answers():
    """Fetch MATL Answers using the StackExchange API."""
    site = Site(ProgrammingPuzzlesampCodeGolf,
                current_app.config['STACK_EXCHANGE_KEY'])

    # We would like answers that contain "MATL" and are tagged with
    # code-golf
    query = {'q': 'MATL',
             'tagged': 'code-golf',
             'body': 'MATL',
             'comments': ''}

    # Grab a collection of MATLAnswers by searching for MATL
    response = site.build('search/excerpts', MATLAnswer, True, query)
    answers = [answer for answer in response]

    # Remove anything with an ID of 0 (a question)
    answers = [answer for answer in answers if answer.id != 0]

    # Now we want to go through and find the ones that are either:
    #
    #   1) Not in the database at all
    #   2) Have had activity since the last check date

    to_fetch = []

    for answer in answers:
        entry = Answer.query.filter(Answer.answer_id == answer.id).first()

        if re.match('MATL[,\s]', answer.body) is None:
            if entry:
                entry.delete()
            continue

        to_fetch.append(answer)

        continue

        # If we don't have an entry yet, then we need to fetch it
        if entry is None or answer.last_activity_date < entry.updated:
            to_fetch.append((answer, entry))

    answers = to_fetch

    users = StackExchangeUser.query.all()
    users = {u.user_id: u for u in users}

    # Get more detailed information on each set of 100 questions
    groups = grouper(100, answers)

    for group in groups:
        ans = site.answers([answer.id for answer in group],
                           filter=ANSWER_FILTER)

        for answer in ans:
            soup = BeautifulSoup(answer.body, 'html.parser')

            code = None

            # Find the shortest codeblock
            for pre in soup.findAll('pre'):
                codeblock = pre.find('code')

                if codeblock:
                    code = codeblock.text.strip()
                    break

            # Skip if we didn't find any source code
            if code is None:
                continue

            # Look up the answer to determine if we need
            a = Answer.query.filter(Answer.answer_id == answer.id).first()

            if a is None:
                a = Answer()

            a.update(answer_id=answer.id,
                     owner_id=answer.owner_id,
                     title=answer.title,
                     question_id=answer.question_id,
                     accepted=answer.is_accepted,
                     created=answer.creation_date,
                     updated=answer.last_activity_date,
                     score=answer.score,
                     source_code=code,
                     url=answer.url)

            # Create the user if it doesn't exist already
            if answer.owner_id not in users:
                owner = site.user(answer.owner_id)
                user = StackExchangeUser.create(user_id=owner.id,
                                                username=owner.display_name,
                                                profile_url=owner.url,
                                                avatar_url=owner.profile_image)

                # Save it for future reference
                users[user.user_id] = user

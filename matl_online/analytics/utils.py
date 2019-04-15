"""Module for retrieving and parsing MATL Answers."""

import re

from bs4 import BeautifulSoup
from stackexchange import Site, ProgrammingPuzzlesampCodeGolf
from stackexchange.models import Answer as StackExchangeAnswer

from matl_online.analytics.models import Answer, StackExchangeUser
from matl_online.settings import config
from matl_online.utils import grouper_iterator

# An Answer filter to use for the SE API so that we get back specific fields
ANSWER_FILTER = '!b0OfNb3Hk1Ze71'

client = Site(
    ProgrammingPuzzlesampCodeGolf,
    config.STACK_EXCHANGE_KEY
)


def filter_invalid_answers(answers):
    """Remove any invalid answers from the retrieved answers."""
    for answer in answers:
        if answer.is_valid():
            yield answer
        else:
            # Delete any invalid record we may have persisted previously
            answer.delete()


def fetch_answer_details(answers):
    """Get more detailed information for each answer."""
    # We batch these into groups of 100 to improve efficiency
    for batch in grouper_iterator(100, answers):
        print('Fetching details for {}'.format(len(batch)))
        lookup = {answer.id: answer for answer in batch}
        details = client.answers(lookup.keys(), filter=ANSWER_FILTER)

        for detail in details:
            answer = lookup[detail.id]
            answer.details = detail
            yield answer


class MATLAnswer(StackExchangeAnswer):
    """A Class for representing a MATL Answer on PPCG."""

    BODY_REGEX = re.compile(r'MATL[,\s]')
    QUERY_PARAMS = {
        'q': 'MATL',
        'tagged': 'code-golf',
        'body': 'MATL',
        'comments': ''
    }

    # This is a default ID to prevent issues when one is not-assigned
    id = 0

    @classmethod
    def refresh(cls):
        """Lookup all MATL answers and update the database records accordingly."""
        for answer in cls.find_all():
            answer.update()

    @classmethod
    def find_all(cls, details=True):
        """Identify all MATL answers on the Code Golf site."""
        answers = client.build('search/excerpts', cls, True, cls.QUERY_PARAMS)
        answers = filter_invalid_answers(answers)

        # If requested, fetch detailed info on these answers
        if details:
            answers = fetch_answer_details(answers)

        for answer in answers:
            yield answer

    def delete(self):
        """Remove any persisted information about this answer."""
        self.__query().delete()

    def update(self):
        """Update the database model representation of this answer."""
        record = self.model() or Answer()

        # Make sure we create the owner record as well
        self.owner

        # Now update the fields we care about
        record.update(
            answer_id=self.id,
            owner_id=self.owner_id,
            title=self.title,
            question_id=self.question_id,
            accepted=self.is_accepted,
            created=self.creation_date,
            updated=self.last_activity_date,
            score=self.score,
            source_code=self.code,
            url=self.url
        )

    def model(self):
        """Underlying database model."""
        return self.__query().first()

    def is_answer(self):
        """Boolean indicating whether this is an answer or not."""
        return self.id != 0

    def is_valid(self):
        """Boolean indicating if an answer is valid."""
        return self.is_answer() and \
            self.BODY_REGEX.match(self.body) is not None and \
            self.code is not None

    @property
    def owner_id(self):
        """Id of the owner of the answer."""
        self.details.owner_id

    @property
    def owner(self):
        """User corresponding to the owner of the answer."""
        owner = StackExchangeUser.from_cache(self.owner_id)

        if owner:
            return owner

        info = client.user(self.owner_id)
        return StackExchangeUser.create(
            user_id=info.id,
            username=info.display_name,
            profile_url=info.url,
            avatar_url=info.profile_image
        )

    @property
    def codeblocks(self):
        """All blocks of code detected in the answer."""
        soup = BeautifulSoup(self.body, 'html.parser')

        blocks = []

        for pre in soup.findAll('pre'):
            codeblock = pre.find('code')

            if codeblock:
                blocks.append(codeblock.text.strip())

        return blocks

    @property
    def code(self):
        """Primary code block."""
        try:
            return self.__code
        except AttributeError:
            pass

        codeblocks = self.codeblocks

        if len(codeblocks) == 0:
            return None

        # The shortest codeblock should be returned
        self.__code = codeblocks.sort(key=len)[0]
        return self.__code

    def __query(self):
        return Answer.query.filter(Answer.answer_id == self.id)

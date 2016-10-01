"""Public-facing analytics dashboard routes."""
import json

from datetime import datetime as dt
from flask import Blueprint, render_template, request
from itertools import groupby

from .models import Answer, StackExchangeUser

blueprint = Blueprint('analytics', __name__, static_folder='../static',
                      url_prefix='/analytics')

# Formats to use when grouping data into date ranges
groupers = {
    'year': ['%Y', '%Y'],
    'month': ['%Y-%m', '%Y-%m'],
    'week': ['%Y-%W-0', '%Y-%W-%w'],
    'day': ['%Y-%m-%d', '%Y-%m-%d']
}


def to_epoch(date):
    """Helper function for converting datetimes to seconds."""
    return (date - dt(1970, 1, 1)).total_seconds()


def group_by_date(date, span):
    """Helper function for grouping by a given time span."""
    read_fmt, write_fmt = groupers[span]
    return to_epoch(dt.strptime(date.strftime(read_fmt), write_fmt))


@blueprint.route('/answer/histogram')
def histogram():
    """View for returning answers grouped by the given interval."""
    span = request.args.get('span', 'week').lower()

    answers = Answer.query.order_by(Answer.created).all()

    result = list()

    for key, group in groupby(answers, lambda x: group_by_date(x.created, span)):
        date = key

        # Get all group members
        answers = list(group)

        # Compute a few metrics here:
        data = {'date': date,
                'answers': len(answers),
                'accepted': sum([a.accepted for a in answers]),
                'score': sum([a.score for a in answers])}

        # Append to the data we will return
        result.append(data)

    # Send a JSON response
    return json.dumps(result), 200


@blueprint.route('/answers')
def answers():
    """A list of all MATL answers that we have stored."""
    output = list()

    for answer in Answer.query.all():
        # Compute various metrics on each answer
        output.append({'title': answer.title,
                       'url': answer.url,
                       'owner': answer.owner.username,
                       'score': answer.score,
                       'created': to_epoch(answer.created)})

    # Send a JSON response
    return json.dumps(output), 200


@blueprint.route('/users')
def userlist():
    """List of all users that have answered a question using MATL."""
    users = list()

    for user in StackExchangeUser.query.all():
        answers = user.answers

        # Compute the cumulative score for all answers
        score = sum([a.score for a in answers])

        users.append({'username': user.username,
                      'avatar': user.avatar_url,
                      'profile': user.profile_url,
                      'answers': len(answers),
                      'score': score})

    # Send a JSON response
    return json.dumps(users), 200


@blueprint.route('/')
def home():
    """Main analytics page."""
    return render_template('analytics.html')

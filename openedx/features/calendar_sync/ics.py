""" Generate .ics files from a user schedule """

from datetime import datetime, timedelta

import pytz
from django.conf import settings
from icalendar import Calendar, Event, vCalAddress, vText

from lms.djangoapps.courseware.courses import get_course_assignments
from openedx.core.djangoapps.site_configuration.helpers import get_value
from openedx.core.djangolib.markup import HTML

from . import get_calendar_event_id


def generate_ics_for_event(uid, summary, url, now, start, organizer_name, organizer_email):
    """
    Generates an ics-formatted bytestring for the given assignment information.

    To pretty-print the bytestring, do: `ics.decode('utf8').replace('\r\n', '\n')`
    """
    # icalendar library: https://icalendar.readthedocs.io/en/latest/
    # ics format spec: https://tools.ietf.org/html/rfc2445
    # ics conventions spec: https://tools.ietf.org/html/rfc5546

    organizer = vCalAddress('mailto:' + organizer_email)
    organizer.params['cn'] = vText(organizer_name)

    event = Event()
    event.add('uid', uid)
    event.add('dtstamp', now)
    event.add('organizer', organizer, encode=0)
    event.add('summary', summary)
    # FIXME description should be translated if we use hardcoded text, once we finalize that text
    event.add('description', HTML('<a href="{url}">Link</a>').format(url=url))
    event.add('dtstart', start)
    event.add('duration', timedelta(0))
    event.add('transp', 'TRANSPARENT')  # available, rather than busy

    cal = Calendar()
    cal.add('prodid', '-//Open edX//calendar_sync//EN')
    cal.add('version', '2.0')
    cal.add('method', 'REQUEST')
    cal.add_component(event)

    return cal.to_ical()


def generate_ics_for_user_course(course_key, user, request):
    """
    Generates ics-formatted bytestrings of all assignments for a given course and user.

    To pretty-print each bytestring, do: `ics.decode('utf8').replace('\r\n', '\n')`

    Returns an iterable of ics files, each one representing an assignment.
    """
    assignments = get_course_assignments(course_key, user, request)
    platform_name = get_value('platform_name', settings.PLATFORM_NAME)
    platform_email = get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    now = datetime.now(pytz.utc)

    return (
        generate_ics_for_event(
            now=now,
            organizer_name=platform_name,
            organizer_email=platform_email,
            start=assignment.date,
            summary=assignment.title,
            uid=get_calendar_event_id(user, str(assignment.block_key), 'due', request.site.domain),
            url=assignment.url,
        )
        for assignment in assignments
    )

"""A python module for scraping the Virginia Tech Timetable of Classes.

This module makes it easy to get data from the Virginia Tech Timetable of
Classes using python. The most important components of the module are the
`search_timetable` function, which directly searches the timetable with the
provided parameters, and the `Course` class, which contains data about a
course. Additionally, `get_crn` makes it easier to search for a specific
course. The two other functions, `get_semesters` and `get_subjects`, make it
possible to check which search parameters are valid.
"""

from collections import defaultdict
from enum import Enum
import re
from typing import Dict, List, Set, Tuple

from pandas import read_html
import pandas.core.series
import requests

__docformat__ = "google"


class Campus(Enum):
    """Represents possible campuses for VT course locations.

    This class is used as a search parameter in `search_timetable` to select a
    campus.
    """

    BLACKSBURG = '0'
    VIRTUAL = '10'


class Day(Enum):
    """Represents days of the week that classes can take place.

    This class is used in `Course` to represent what days of the week the
    course takes place.
    """

    MONDAY = 'Monday'
    TUESDAY = 'Tuesday'
    WEDNESDAY = 'Wednesday'
    THURSDAY = 'Thursday'
    FRIDAY = 'Friday'
    SATURDAY = 'Saturday'
    SUNDAY = 'Sunday'
    ARRANGED = 'Arranged'


class Modality(Enum):
    """Represents possible VT course modalities.

    This class is used as a search parameter in `search_timetable` to select a
    modality.
    """

    ALL = '%'
    IN_PERSON = 'A'
    HYBRID = 'H'
    ONLINE_SYNC = 'N'
    ONLINE_ASYNC = 'O'


class Pathway(Enum):
    """Represents possible Pathways designations for VT courses.

    This class is used as a search parameter in `search_timetable` to select a
    Pathways category.
    """

    ALL = 'AR%'
    CLE_1 = 'AR01'
    CLE_2 = 'AR02'
    CLE_3 = 'AR03'
    CLE_4 = 'AR04'
    CLE_5 = 'AR05'
    CLE_6 = 'AR06'
    CLE_7 = 'AR07'
    PATH_1A = 'G01A'
    PATH_1F = 'G01F'
    PATH_2 = 'G02'
    PATH_3 = 'G03'
    PATH_4 = 'G02'
    PATH_5A = 'G02'
    PATH_5F = 'G02'
    PATH_6A = 'G06A'
    PATH_6D = 'G06D'
    PATH_7 = 'G07'


class SectionType(Enum):
    """Represents possible types of instruction for VT courses.

    This class is used as a search parameter in `search_timetable` to select a
    type of section.
    """

    ALL = '%'
    INDEPENDENT_STUDY = '%I%'
    LAB = '%B%'
    LECTURE = '%L%'
    RECITATION = '%C%'
    RESEARCH = '%R%'
    ONLINE = 'ONLINE'


class Semester(Enum):
    """Represents different semesters for VT classes.

    This class is used as a search parameter in `search_timetable` to select a
    semester.
    """

    SPRING = '01'
    SUMMER = '06'
    FALL = '09'
    WINTER = '12'


class Status(Enum):
    """Represents search parameter for available seats in classes.

    This class is used as a search parameter in `search_timetable` to select
    whether all classes should be searched or only classes with open seats
    should be searched.
    """

    ALL = ''
    OPEN = 'on'


class Course:
    """Represents a course at VT.

    This class is used as a container for data about courses at Virginia Tech.
    """

    _section_type_dct = {'I': SectionType.INDEPENDENT_STUDY,
                         'B': SectionType.LAB,
                         'L': SectionType.LECTURE,
                         'C': SectionType.RECITATION,
                         'R': SectionType.RESEARCH,
                         'O': SectionType.ONLINE}
    _modality_dct = {'Face-to-Face Instruction': Modality.IN_PERSON,
                     'Hybrid (F2F & Online Instruc.)': Modality.HYBRID,
                     'Online with Synchronous Mtgs.': Modality.ONLINE_SYNC,
                     'Online: Asynchronous': Modality.ONLINE_ASYNC}
    _day_dct = {'M': Day.MONDAY, 'T': Day.TUESDAY, 'W': Day.WEDNESDAY,
                'R': Day.THURSDAY, 'F': Day.FRIDAY, 'S': Day.SATURDAY,
                'U': Day.SUNDAY, '(ARR)': Day.ARRANGED}

    def __init__(self, year: str, semester: Semester,
                 timetable_data: pandas.core.series.Series,
                 extra_class_data: pandas.core.series.Series) -> None:
        """ A constructor for `Course`.

        Args:
            year:
                string representing the year in which the course is taking
                place.
            semester:
                `Semester` representing the semester in which the course is
                taking place.
            timetable_data:
                `pandas.Series` representing the data scraped from the
                timetable.
            extra_class_data:
                Optional `pandas.Series` representing the days and times of
                additional classes scraped from the timetable.
        """

        subject, code = re.match(r'(.+)-(.+)', timetable_data[1]).group(1, 2)

        if semester == Semester.SUMMER:
            name = re.search(r'- \d{2}-[A-Z]{3}-\d{4}(.+)$',
                             timetable_data[2]).group(1)
        else:
            name = timetable_data[2]

        section_type = self._section_type_dct[
            'O' if re.match(r'ONLINE COURSE', timetable_data[3]) else
            re.match(r'[LBICR]', timetable_data[3]).group(0)]

        modality = (self._modality_dct[timetable_data[4]] if
                    timetable_data[4] in self._modality_dct else None)

        class_dct = defaultdict(set)
        for day in [self._day_dct[d] for d in timetable_data[8].split()]:
            if day == Day.ARRANGED:
                continue
            class_dct[day].add((timetable_data[9], timetable_data[10],
                                timetable_data[11]))
        if (extra_class_data is not None and
                extra_class_data[4] == '* Additional Times *'):
            for day in [self._day_dct[d] for d in extra_class_data[8].split()]:
                class_dct[day].add((extra_class_data[9], extra_class_data[10],
                                    extra_class_data[11]))
        class_dct = dict(class_dct)

        self._course_data = {'year': year, 'semester': semester,
                             'crn': timetable_data[0][:5],
                             'subject': subject,
                             'code': code,
                             'name': name,
                             'section_type': section_type,
                             'modality': modality,
                             'credit_hours': timetable_data[5],
                             'capacity': timetable_data[6],
                             'professor': timetable_data[7],
                             'schedule': class_dct}

    def __str__(self):
        return ''.join(
            f'{d}: {self._course_data[d]}, ' for d in self._course_data)[:-2]

    def get_year(self) -> str:
        return self._course_data['year']

    def get_semester(self) -> Semester:
        return self._course_data['semester']

    def get_crn(self) -> str:
        return self._course_data['crn']

    def get_subject(self) -> str:
        return self._course_data['subject']

    def get_code(self) -> str:
        return self._course_data['code']

    def get_name(self) -> str:
        return self._course_data['name']

    def get_type(self) -> SectionType:
        return self._course_data['section_type']

    def get_modality(self) -> Modality:
        return self._course_data['modality']

    def get_credit_hours(self) -> str:
        return self._course_data['credit_hours']

    def get_capacity(self) -> str:
        return self._course_data['capacity']

    def get_professor(self) -> str:
        return self._course_data['professor']

    def get_schedule(self) -> Dict[Day, Set[Tuple[str, str, str]]]:
        return self._course_data['schedule']

    def has_open_spots(self) -> bool:
        return True if search_timetable(self.get_year(), self.get_semester(),
                                        crn=self.get_crn(),
                                        status=Status.OPEN) else False


class InvalidRequestException(Exception):
    """Raised when the timetable POST request results in an error."""

    pass


class InvalidSearchException(Exception):
    """Raised when invalid search parameters are provided to the timetable."""

    pass


def get_crn(year: str, semester: Semester, crn: str) -> Course:
    """Fetches a course with the provided CRN from the timetable.

    Args:
        year:
            string representing the year in which the course is taking place.
        semester:
            Semester object representing the semester in which the course is
            taking place.
        crn:
            string representing the Course Request Number of the course.

    Returns:
        A `Course` if there is a course with the provided CRN in the
        provided year and semester, otherwise None.
    """

    crn_search = search_timetable(year, semester, crn=crn)
    return crn_search[0] if crn_search else None


def get_semesters() -> Set[Tuple[str, str]]:
    """Fetches the semesters listed in the timetable.

    Returns:
        A set of length-2 tuples representing the semesters listed in the
        timetable. The first element of each tuple is the semester, and the
        second element of each tuple is the year.
    """

    semester_dct = {'Spring': Semester.SPRING, 'Summer': Semester.SUMMER,
                    'Fall': Semester.FALL, 'Winter': Semester.WINTER}
    return set((semester_dct[m.group(1)], m.group(2)) for m in re.finditer(
        r'<OPTION VALUE="\d{6}">([A-Z][a-z]+) (\d+)<\/OPTION>',
        _make_request(request_type='GET')))


def get_subjects() -> Set[Tuple[str, str]]:
    """Fetches the course subjects listed in the timetable.

    Returns:
        A set of length-2 tuples representing the course subjects listed in the
        timetable. The first element of each tuple is the abbreviation of the
        subject name, and the second element of each tuple is is the full
        subject name.
    """

    return set((m.group(1), m.group(2)) for m in
               re.finditer(r'\("([A-Z]+) - (.+?)"',
                           _make_request(request_type='GET')))


def search_timetable(year: str, semester: Semester,
                     campus: Campus = Campus.BLACKSBURG,
                     pathway: Pathway = Pathway.ALL, subject: str = '',
                     section_type: SectionType = SectionType.ALL,
                     code: str = '', crn: str = '',
                     status: Status = Status.ALL,
                     modality: Modality = Modality.ALL) -> List[Course]:
    """Performs a search of the timetable with the given arguments.

    Args:
        year:
            string representing the year in which the course is taking place.
        semester:
            `Semester` representing the semester in which the course is taking
            place.
        campus:
            `Campus` representing the campus at which the course is taking
            place.
        pathway:
            `Pathway` representing the Pathway/CLE designation of the course.
        subject:
            string representing the subject of the course.
        section_type:
            `SectionType` representing the section type of the course.
        code:
            string representing the code number of the course.
        crn:
            string representing the Course Request Number of the course.
        status:
            `Status` representing whether the course needs to have open spots
            or not.
        modality:
            `Modality` representing the modality of the course.

    Returns:
        List of courses returned by the search.
    """

    term_year = ((str(int(year) - 1) if semester == Semester.WINTER else year)
                 + semester.value)
    subject = '%' if subject == '' else subject
    request = _make_request(request_type='POST',
                            request_data={'CAMPUS': campus,
                                          'TERMYEAR': term_year,
                                          'CORE_CODE': pathway,
                                          'subj_code': subject,
                                          'SCHDTYPE': section_type,
                                          'CRSE_NUMBER': code,
                                          'crn': crn,
                                          'open_only': status,
                                          'sess_code': modality,
                                          })
    if request == '':
        return []

    request_data = read_html(request)[4]
    course_list = []
    for i in range(1, request_data.shape[0]):
        if isinstance(request_data.iloc[i][0], str):
            course_list.append(Course(year, semester, request_data.iloc[i],
                                      request_data.iloc[i + 1] if
                                      request_data.shape[0] > i + 1 else None))
    return course_list


def _make_request(request_type: str,
                  request_data: Dict[str, str] = None) -> str:
    url = 'https://apps.es.vt.edu/ssb/HZSKVTSC.P_ProcRequest'
    if request_type == 'POST':
        for r in request_data:
            request_data[r] = (request_data[r].value if
                               issubclass(type(request_data[r]), Enum) else
                               request_data[r])
        request = requests.post(url, request_data)

        if 'THERE IS AN ERROR WITH YOUR REQUEST' in request.text:
            raise InvalidRequestException(
                'The search parameters provided were invalid')
        if 'There was a problem with your request' in request.text:
            if 'NO SECTIONS FOUND FOR THIS INQUIRY' in request.text:
                return ''
            else:
                course_not_found_message = re.search(
                    r'<b class=red_msg><li>(.+)</b>', request.text).group(1)
                raise InvalidSearchException(course_not_found_message)

        return request.text
    elif request_type == 'GET':
        return requests.get(url).text
    else:
        raise ValueError('Invalid request type')

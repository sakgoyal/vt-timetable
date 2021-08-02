# vt-timetable

A python module for scraping the Virginia Tech Timetable of Classes.

This module makes it easy to get data from the Virginia Tech Timetable of
Classes using python. The most important components of the module are the
`search_timetable` function, which directly searches the timetable with the
provided parameters, and the `Course` class, which contains data about a
course. Additionally, `get_crn` makes it easier to search for a specific course
and `get_subjects` makes it easy to get a list of all the course subjects in
the timetable.

Documentation can be found
[here](https://leodiperna.com/projects/vt-timetable/documentation).

## Getting started

This module can be installed from the Python Package Index.

```console
pip install vt-timetable
```

After installing the module, it can be imported with:

```python
import vtt
```

## Examples

Getting data about CRN 83075 for Fall 2021, and checking if there are any open
spots:

```python
course = get_crn('2021', Semester.FALL, '83075')
course.has_open_spots()
```

Getting a list of all MATH 2114 sections for Fall 2021 that are taking place in
person:

```python
search_timetable('2021', Semester.FALL, subject='MATH', code='2114',
                 modality=Modality.IN_PERSON)
```
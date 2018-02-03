#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Electronic preprints approved for publication after moderation"""


class Paper(object):
    """Electronic preprints approved for publication after moderation"""

    def __init__(self, page_url, title, authors_list, submission_date, abstract, subjects,
                 comments=None):
        """
        :param str page_url:
        :param str title:
        :param str authors_list:
        :param str submission_date:
        :param str abstract:
        :param str subjects:
        :param str comments:
        """
        self._page_url = page_url
        self._code = page_url[page_url.rfind('/') + 1:]
        self._title = title
        self._authors_list = authors_list
        self._submission_date = submission_date
        self._abstract = abstract
        self._subjects = subjects
        self._comments = comments

    @property
    def code(self):
        """
        :return str:
        """
        return self._code

    @property
    def page_url(self):
        """
        :return str:
        """
        return self._page_url

    @property
    def title(self):
        """
        :return str:
        """
        return self._title

    @property
    def authors_list(self):
        """
        :return str:
        """
        return self._authors_list

    @property
    def submission_date(self):
        """
        :return str:
        """
        return self._submission_date

    @property
    def abstract(self):
        """
        :return str:
        """
        return self._abstract

    @property
    def subjects(self):
        """
        :return str:
        """
        return self._subjects

    @property
    def comments(self):
        """
        :return str:
        """
        return self._comments

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Small script to dump  basic information about a paper fron arxiv.org portal"""

import argparse
import glob
import json
import logging
import os
import shutil
import re
import requests

from paper import Paper

DESCRIPTION_INFO = 'Crawler for dump papers from arxiv.org'
HELP_CODE_AREA = 'Science code area category (e.g: cs, cs.CE, physics, ...)'
HELP_OUTPUT_FOLDER = 'Folder where the dump will be save'

ARXIV_URL = 'https://arxiv.org'
ARXIV_ABS_PAPER_URL = ''.join([ARXIV_URL, '/abs/{PAPER_CODE}'])
ARXIV_LIST_RECENT_PAGE = ''.join([ARXIV_URL, '/list/{CODE_AREA}/recent'])

REQUEST_STATUS_OK = requests.status_codes.codes.get('OK')
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

FILE_MASK = '{name}.{extension}'
DUMP_FILE_EXTENSION = 'json'

PAGE_URL_KEY = 'PAGE_URL_KEY'
PAGE_CONTENT_KEY = 'PAGE_CONTENT_KEY'

logging.basicConfig(format='%(asctime)s %(message)s')
LOG = logging.warning


def main():
    """Dump papers from arxiv.org"""
    args = init_args()
    papers_count_total = 0

    for code_area in args.codes_areas:
        # It will be used to save all new papers found
        folder_path = os.path.join(args.output_folder, code_area)
        create_path(folder_path)

        papers_count = 0

        recent_page = get_recent_papers_page(code_area).get(PAGE_CONTENT_KEY)
        papers_urls = extract_papers_urls(recent_page)

        for paper_url in papers_urls:
            paper_code = extract_paper_code(paper_url)

            if not is_file_exists(args.output_folder, paper_code):
                paper_page = get_page_content(paper_url)
                paper = generate_paper_object(paper_page)
                save_new_paper_at_json(folder_path, paper)

                papers_count += 1
                papers_count_total += 1

        LOG('Number of papers saved for code {}: #{}'.format(code_area, papers_count))

    LOG('Total number of papers saved: #{}'.format(papers_count_total))


def init_args():
    """
    :return argparse.Namespace: Arguments from argparse
    """
    parser = argparse.ArgumentParser(prog=DESCRIPTION_INFO, description=DESCRIPTION_INFO)
    parser.add_argument(
        '--codes_areas', type=str, nargs='+', help=HELP_CODE_AREA, required=True
    )
    parser.add_argument(
        '--output_folder', type=str, help=HELP_OUTPUT_FOLDER, default=SCRIPT_PATH
    )
    args = parser.parse_args()

    return args


def get_page_content(page_url):
    """
    :param str page_url:
    """
    LOG('Getting page content: {}'.format(page_url))
    response = requests.get(page_url)

    if response and response.status_code == REQUEST_STATUS_OK:
        return dict(PAGE_URL_KEY=page_url, PAGE_CONTENT_KEY=response.text)


def get_recent_papers_page(code_area):
    """
    :param str code_area:
    :return str:
    """
    url = ARXIV_LIST_RECENT_PAGE.format(CODE_AREA=code_area)
    return get_page_content(url)


def extract_papers_urls(page_content):
    """
    :param str page_content:
    :return list:
    """
    LOG('Extracting papers url')
    expression = r'a\shref\=\"\/abs\/(\d*\.\d*)\"'
    papers_codes = re.findall(expression, page_content)
    return [ARXIV_ABS_PAPER_URL.format(PAPER_CODE=paper_code) for paper_code in papers_codes]


def extract_paper_code(url):
    """
    :param str urls:
    :return str:
    """
    return url[url.rfind('/') + 1:]


def get_paper_title(paper_page_content):
    """
    :param str paper_page_content:
    :return str:
    """
    expression = r'\<meta\sname\=\"citation\_title\"\scontent\=\"(.+)\"\s*/>'
    title = re.findall(expression, paper_page_content)

    if title:
        return title[0]


def get_paper_author(paper_page_content):
    """
    :param str paper_page_content:
    :return str:
    """
    expression = r'\<meta\sname\=\"citation\_author\"\scontent\=\"(.+)\"\s*/>'
    author = re.findall(expression, paper_page_content)

    if author:
        return author


def get_paper_date(paper_page_content):
    """
    :param str paper_page_content:
    :return str:
    """
    expression = r'\<meta\sname\=\"citation\_date\"\scontent\=\"(.+)\"\s*/>'
    date = re.findall(expression, paper_page_content)

    if date:
        return date[0]


def get_paper_abstract(paper_page_content):
    """
    :param str paper_page_content:
    :return str:
    """
    start_target = 'Abstract:</span>'
    start_target_len = len(start_target)

    end_target = '</blockquote>'

    start = paper_page_content.find(start_target)
    end = paper_page_content.find(end_target)

    if start and end:
        return paper_page_content[start + start_target_len:end].strip()


def get_paper_subjects(paper_page_content):
    """
    :param str paper_page_content:
    :return str:
    """
    expression = r'<td.*subjects.*\"\>.*\<\/span\>\;(.*)\<\/td\>'
    subjects = re.findall(expression, paper_page_content)

    if subjects:
        subjects = subjects[0].strip()
        return [subject.strip() for subject in subjects.split(';')]


def get_paper_comments(paper_page_content):
    """
    :param str paper_page_content:
    :return str:
    """
    expression = r'<td.*comment.*\>(.*)\<\/td\>'

    try:
        comments = re.findall(expression, paper_page_content)
    except TypeError:
        comments = None

    if comments:
        return comments[0].strip()


def generate_paper_object(paper_page_content_dict):
    """
    :param dict paper_page_content_dict:
    :return list:
    """
    paper_page_url = paper_page_content_dict.get(PAGE_URL_KEY)
    paper_page_content = paper_page_content_dict.get(PAGE_CONTENT_KEY)
    LOG('Generating paper: {}'.format(paper_page_url))

    paper = Paper(
        page_url=paper_page_url,
        title=get_paper_title(paper_page_content),
        authors_list=get_paper_author(paper_page_content),
        submission_date=get_paper_date(paper_page_content),
        abstract=get_paper_abstract(paper_page_content),
        subjects=get_paper_subjects(paper_page_content),
        comments=get_paper_comments(paper_page_content)
    )

    return paper


def read_file(file_path):
    """
    :param str file_path:
    """
    opened_file_content = None

    try:
        with open(file_path, 'r') as opened_file:
            LOG('Reading file: {}'.format(file_path))
            opened_file_content = ''.join(opened_file.readlines())
    except Exception:
        pass

    return opened_file_content


def create_path(path, remove=False):
    """
    :param str path:
    :param bool remove:
    """
    if os.path.exists(path) and remove:
        shutil.rmtree(path)

    try:
        os.makedirs(path)
        LOG('Creating folder: {}'.format(path))
    except Exception:
        pass


def find_files(start_point, file_name):
    """
    :param str start_point: Where the search should start from
    :param str file_name: File name to be find
    :return str / list: Path / List of paths with what matches
    """
    return glob.glob('{}/**/{}'.format(start_point, file_name), recursive=True)


def is_file_exists(folder_path, file_name):
    """
    :param str folder_path:
    :param str file_name:
    """
    found = False
    file_name = FILE_MASK.format(name=file_name, extension=DUMP_FILE_EXTENSION)
    files_paths = find_files(folder_path, '*')

    for file_path in files_paths:
        found = file_name in file_path

        if found:
            break

    return found


def save_new_paper_at_json(folder_path, paper):
    """
    :param str folder_path:
    :param str code_area:
    :param Paper paper:
    """
    file_path = os.path.join(
        folder_path, FILE_MASK.format(name=paper.code, extension=DUMP_FILE_EXTENSION)
    )

    with open(file_path, 'w') as opened_file:
        LOG('Saving new paper: {}'.format(file_path))
        json_content = dict(
            paper_code=paper.code,
            paper_page_url=paper.page_url,
            paper_title=paper.title,
            paper_authors_list=paper.authors_list,
            paper_submission_date=paper.submission_date,
            paper_abstract=paper.abstract,
            paper_comments=paper.comments,
            paper_subjects=paper.subjects,
        )
        opened_file.write(json.dumps(json_content, indent=4, separators=(', ', ': ')))


if __name__ == '__main__':
    main()

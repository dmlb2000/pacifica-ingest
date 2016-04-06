"""
    testable utilities for ingest
"""

from urlparse import parse_qs
import json

import pycurl
from StringIO import StringIO

import cgi
import os
import sys
import io

# pylint: disable=bare-except

def get_job_id(environ):
    """
    parse the parameters for a request from the environ dictionary
    """
    try:
        args = parse_qs(environ['QUERY_STRING'])

        if args:
            job_id = long(args.get('job_id', [''])[0])
            return job_id

        return (None, None)

    except:
        return (None, None)

def valid_request(environ):
    """
    catch and handle bogus requests (ex. faveicon)
    """
    info = environ['PATH_INFO']
    return info == '/get_state'


def create_invalid_return():
    """
    create an error message
    """
    status = '404 NOT FOUND'

    response_body = ''

    response_headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body)))
    ]

    return (status, response_headers, response_body)

def create_return_params(response_body):
    """
    creates return parameters
    """

    status = '200 OK'

    response_headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body)))
    ]

    return (status, response_headers, response_body)

def create_state_return(record):
    """
    creates the dictionary containing the start and stop index
    packs the message components
    """
    state = {'state' : record.state, 'task': record.task, 'task_percent': str(record.task_percent)}
    response_body = json.dumps(state)

    return create_return_params(response_body)


def get_unique_id():
    """
    returns a unique job id from the id server
    """

    buf = StringIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, 'http://127.0.0.1:8051/getid?range=1&mode=upload_job')
    curl.setopt(curl.WRITEDATA, buf)
    curl.perform()
    curl.close()

    body = buf.getvalue()

    info = json.loads(body)

    job_id = info['startIndex']

    return (job_id, body)

def rename_bundle(environ, job_id):
    """
    receive the tar file and save it locally
    """
    try:

        if environ['REQUEST_METHOD'] == 'POST':

            ctype, pdict = cgi.parse_header( environ['CONTENT_TYPE']) 

            path = environ['HTTP_X_FILE']

            dir = os.path.dirname(path)

            name = str(job_id) + ".tar"
            name = os.path.join(dir, name)

            os.rename(path, name)

            return name
    

    except Exception, e:
        print e.message


def receive(environ, job_id):
    """
    receive the tar file and save it locally
    """
    try:
        if environ['REQUEST_METHOD'] == 'POST':
            dir = 'c:\\temp'
            name = str(job_id) + ".tar"
            name = os.path.join(dir, name)
            fo = open(name, 'wb')

            BLOCK_SIZE = 1024 * 1024
            content_length = int(environ['CONTENT_LENGTH'])

            print "content length " + str(content_length)

            while content_length > 0:
                if content_length > BLOCK_SIZE:
                    buf = environ['wsgi.input'].read(BLOCK_SIZE)
                else:
                    buf = environ['wsgi.input'].read(content_length)

                fo.write(buf)
                content_length -= len(buf)
            fo.close


    except Exception, e:
        print e.message





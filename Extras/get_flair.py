#!/usr/bin/python
 
"""Tool for downloading flair from reddit to a local csv file.
 
Example:
 
$ ./flairsync.py -c intortus.cookie example test.csv
Connecting to http://www.reddit.com ...
reddit username: intortus
reddit password:
Fetching current flair from site ...
Done!
$ cat test.csv
user,css
"""
 
import argparse
import csv
import getpass
import htmlentitydefs
import logging
import os
import re
import sys
import time
 
import redditclient
 
def parse_args():
    parser = argparse.ArgumentParser(
        description='download subreddit flair to a csv file')
 
    parser.add_argument('subreddit', metavar='SUBREDDIT')
    parser.add_argument('csvfile', metavar='CSVFILE')
 
    parser.add_argument('-A', '--http_auth', default=False, const=True,
                        action='store_const',
                        help='set if HTTP basic authentication is needed')
    parser.add_argument('-b', '--batch_size', type=int, default=100,
                        help='number of users to read at a time from the site')
    parser.add_argument('-c', '--cookie_file',
                        help='if given, save session cookie in this file')
    parser.add_argument('-H', '--host', default='http://www.reddit.com',
                        help='URL of reddit API server')
    parser.add_argument('-v', '--verbose', default=False, const=True,
                        action='store_const',
                        help='emit more verbose logging')
    return parser.parse_args()
 
def log_in(host, cookie_file, use_http_auth):
    options = dict(user_agent='flairsync')
    if use_http_auth:
        http_user = raw_input('HTTP auth username: ')
        http_password = getpass.getpass('HTTP auth password: ')
        options.update(
            _http_user=http_user, _http_password=http_password)
    client = redditclient.RedditClient(host, cookie_file, **options)
    while not client.log_in():
        print 'login failed'
    return client
 
def flair_from_reddit(client, subreddit, batch_size):
    return [(r[0], r[2]) for r in client.flair_list(subreddit, batch_size=batch_size)]
 
def configure_logging():
    class LoggingFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            timestamp = time.strftime(datefmt)
            return timestamp % dict(ms=(1000 * record.created) % 1000)
 
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = LoggingFormatter(
        '%(levelname).1s%(asctime)s: %(message)s',
        '%m%d %H:%M:%S.%%(ms)03d')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
 
def sync_flair(config):
    print 'Connecting to %s ...' % config.host
    client = log_in(config.host, config.cookie_file, config.http_auth)
 
    print 'Fetching current flair from site ...'
    reddit_flair = flair_from_reddit(client, config.subreddit,
                                     config.batch_size)
 
    writer = csv.writer(open(config.csvfile, 'wb'))
    writer.writerows(reddit_flair)
 
    print 'Done!'
 
def main():
    config = parse_args()
    if config.verbose:
        configure_logging()
    return sync_flair(config)
 
if __name__ == '__main__':
    main()

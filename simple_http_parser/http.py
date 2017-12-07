# -*- coding: utf-8 -


"""
1. parser socket http sticky package with content_length in Header
"""


import re


class HttpStream(object):
    __vre = re.compile("HTTP/(?P<p>\d+).(?P<m>\d+) (?P<n>\d{3}) (?P<s>\w+)")
    __buf = ''
    __res = []

    def __init__(self, stream):
        self.stream = stream

    def __version_match(self):
        match = re.search(self.__class__.__vre, self.__class__.__buf)

        return match

    def __version_match_expand(self, match):
        tpl = 'HTTP/\g<p>.\g<m> \g<n> \g<s>'

        return match.expand(tpl)

    def parser(self, data):
        end_flag = '\r\n'*2

        self.__class__.__buf += data
        if data.endswith(end_flag):
            return
        match = self.__version_match()
        if not match:
            return

        match_str = self.__version_match_expand(match)
        strs_list = self.__class__.__buf.split(match_str)

        data_dpos = 0
        for item in strs_list:
            data_dpos = data_dpos + len(match_str) + 2 + len(item)
            if end_flag in item:
                json_data = item.split(end_flag)[-1]
                self.__class__.__res.append(json_data)
        self.__class__.__buf = self.__class__.__buf[data_dpos:]

    def read(self, buffer_size=4096):
        b = bytearray(buffer_size)
        recved = self.stream.readinto(b)
        del b[recved:]
        data = bytes(b)

        self.parser(data)

    @property
    def body(self):
        while True:
            if not self.__class__.__res:
                yield ''
            yield self.__class__.__res.pop()


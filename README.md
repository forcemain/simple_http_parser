# simple_http_paser
#### 简单介绍:
>[simple_http_paser](https://github.com/xmdevops/simple_http_paser) 主要用于解析Socket Http Response,优雅接收异步服务端粘包,兼容PY2.6+

***


#### 开发环境:
> SY_ENV: MacOS 10.12.6 \
> PY_ENV: Python2.7.10 

***

#### 快速安装:
`git clone https://github.com/xmdevops/simple_http_paser`
`cd simple_http_paser`
`python setup.py install`

***

#### 使用方法:
```python
#! -*- coding: utf-8 -*-


import json
import time
import random
import pprint
import base64
import socket
import hashlib


from threading import Thread
from Queue import Queue, Empty
from http_parser.http import HttpStream
from http_parser.reader import SocketReader


class AsyncQThread(Thread):
    def __init__(self, cls, func, *args, **kwargs):
        super(AsyncQThread, self).__init__()
        self.cls = cls
        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.result = []

    def run(self):
        self.result = self.func(*self.args, **self.kwargs)

    def get_result(self):
        return self.result


def auto_refresh_token(func):
    def wrapper(self, *args, **kwargs):
        if self.token is None:
            self.auth_login()
        return func(self, *args, **kwargs)
    return wrapper


class QueryEntrance(object):
    MI = 1
    MX = pow(2, 31)

    __queuemap = {}
    __instance = None

    def __init__(self, host=None, port=None, username=None, password=None):
        self.host = host
        self.port = port
        self.token = None
        self.nonce = None
        self.queue = Queue()

        self.username = username
        self.password = password

        self.qsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.dispatch()

    # Single Case
    def __new__(cls, *args, **kwargs):
        cls.__instance = cls.__instance or object.__new__(cls, *args, **kwargs)

        return cls.__instance

    def __post(self, uri, **kwargs):
        header_list = map(lambda s: '{0}: {1}'.format(s[0], s[1]), kwargs['headers'].iteritems())
        post_nums = 0
        limit_num = 3

        post_data = [
            'POST {0} HTTP/1.1'.format(uri),
            '\r\n'.join(header_list),
            '\r\n{0}'.format(kwargs['body'])
        ]
        while True:
            try:
                self.qsock.sendall('\r\n'.join(post_data))
                break
            except socket.error as e:
                if post_nums > limit_num:
                    print 'sendall with exception {0} times, failed, exp={1}'.format(limit_num, e)
                    break
                try:
                    self.qsock.connect((self.host, self.port))
                except socket.error:
                    pass
                # 断开连接重新获取Token
                self.token = None
            post_nums += 1

    def __randomid(self):
        pre_id = random.randint(self.__class__.MI, self.__class__.MX)
        while True:
            while True:
                ntx_id = random.randint(self.__class__.MI, self.__class__.MX)
                if ntx_id != pre_id:
                    break
            pre_id = ntx_id
            yield ntx_id

    def __hex_md5s(self, md5):
        hex_str_list = []
        for i in xrange(0, len(md5), 2):
            i_hex = chr(int(md5[i: i+2], 16))
            hex_str_list.append(i_hex)

        return ''.join(hex_str_list)

    def __enc_pass(self):
        pass_str = '{0}{1}'.format(self.nonce, self.password)
        pass_md5 = hashlib.md5(pass_str).hexdigest()
        pass_md5 = self.__hex_md5s(pass_md5)
        pass_b64 = base64.b64encode(pass_md5)

        return pass_b64

    def dispatch(self):
        def update_queuemap():
            while True:
                msg_sid, msg_len, msg_res = self.queue.get()
                self.__class__.__queuemap.update({msg_sid: {'msg_len': msg_len, 'msg_res': msg_res}})

        def consum_queuemap():
            while True:
                count = 0
                while True:
                    try:
                        r = SocketReader(self.qsock)
                        s = HttpStream(r)
                        s.read(4096)
                        json_data = s.body.next()
                        print '=' * 100
                        print json_data
                        print '=' * 100
                    except socket.error:
                        continue
                    try:
                        dict_data = json.loads(json_data)
                    except (TypeError, ValueError):
                        # may be empty data.
                        continue

                    count += 1
                    sid = dict_data['id']
                    sid_data = self.__class__.__queuemap[sid]

                    sid_data['msg_res'].put(dict_data)
                    if count == sid_data['msg_len']:
                        break

        p = Thread(target=update_queuemap)
        p.setDaemon(True)
        p.start()
        c = Thread(target=consum_queuemap)
        c.setDaemon(True)
        c.start()

    def auth_nonce(self):
        method = 'xmcloud/service/login'
        sid = self.__randomid().next()
        url = '/{0}'.format(method)
        body = {
            'id': sid,
            'jsonrpc': '2.0',
            'method': method,
            'params': {'username': self.username}
        }
        js_body = json.dumps(body)
        headers = {
            'Host': '{0}:{1}'.format(self.host, self.port),
            'Accept': '*/*',
            'Connection': 'Keep-alive',
            'charsets': 'utf-8',
            'Content-Type': 'application/json',
            'Content-Length': len(js_body),
        }

        res = Queue()
        self.queue.put((sid, 1, res))
        self.__post(url, method='POST', headers=headers, body=js_body)

        count = 0
        while True:
            count += 1
            rec = res.get()
            self.nonce = rec['result']['nonce']
            if count == 1:
                break

    def auth_login(self):
        self.auth_nonce()

        method = 'xmcloud/service/login'
        sid = self.__randomid().next()
        url = '/{0}'.format(method)
        body = {
            'id': sid,
            'jsonrpc': '2.0',
            'method': method,
            'params': {
                'username': self.username,
                'password': self.__enc_pass()
            }
        }
        js_body = json.dumps(body)
        headers = {
            'Host': '{0}:{1}'.format(self.host, self.port),
            'Accept': '*/*',
            'Connection': 'Keep-alive',
            'charsets': 'utf-8',
            'Content-Type': 'application/json',
            'Content-Length': len(js_body),
        }

        res = Queue()
        self.queue.put((sid, 1, res))
        self.__post(url, method='POST', headers=headers, body=js_body)

        count = 0
        while True:
            count += 1
            rec = res.get()
            self.token = rec['result']['token']
            if count == 1:
                break

    @auto_refresh_token
    def query(self, params):
        method = 'xmcloud/service/status/query'
        sid = self.__randomid().next()
        url = '/{0}'.format(method)
        body = {
            'id': sid,
            'jsonrpc': '2.0',
            'method': 'xmcloud/service/status/query',
            'params': params,
            'token': self.token
        }
        js_body = json.dumps(body)
        headers = {
            'Host': '{0}:{1}'.format(self.host, self.port),
            'Accept': '*/*',
            'Connection': 'Keep-alive',
            'charsets': 'utf-8',
            'Content-Type': 'application/json',
            'Content-Length': len(js_body),
        }

        res = Queue()
        self.queue.put((sid, len(params), res))
        self.__post(url, method='POST', headers=headers, body=js_body)

        return [sid]

    def query_one_with_one_mode(self, uuid, mode):
        sid_list = []
        params = [{'uuid': uuid, 'mode': mode, 'auth': ''}]
        sid_list.extend(self.query(params))

        return sid_list

    def query_one_with_all_mode(self, uuid):
        sid_list = []
        modes = ['eznatv1', 'eznatv2', 'dss', 'rps', 'tps', '']
        sid_list.extend(self.query_one_with_more_mode(uuid, *modes))

        return sid_list

    def query_one_with_more_mode(self, uuid, *modes):
        sid_list = []
        for mode in modes:
            sid_list.extend(self.query_one_with_one_mode(uuid, mode))

        return sid_list

    def map(self, *sids):
        rlist = []

        def target(s_id):
            count = 0
            slist = []
            if s_id not in self.__class__.__queuemap:
                return slist
            sid_data = self.__class__.__queuemap[s_id]
            while True:
                try:
                    rec = sid_data['msg_res'].get(timeout=10)
                    slist.append(rec)
                    count += 1
                    if count == sid_data['msg_len']:
                        break
                except Empty:
                    break

            return slist

        tlist = []
        for sid in sids:
            t = AsyncQThread(self, target, sid)
            tlist.append(t)
            t.start()
        for t in tlist:
            t.join()
        for t in tlist:
            rlist.extend(t.get_result())

        return rlist


if __name__ == '__main__':
    q = QueryEntrance(host='<host>', port=9355, username='<username>', password='<password>')
    cur_time = time.time()
    sid_list = q.query_one_with_all_mode('<uuid>')
    pprint.pprint(q.map(*sid_list))
    nxt_time = time.time()

    print 'notice: used {0} seconds'.format(nxt_time-cur_time)
```
***

#### Copyright:
2017.12.07  (c) Limanman <xmdevops@vip.qq.com>

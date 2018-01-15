# simple_http_paser
#### 简单介绍:
>[simple_http_paser](https://github.com/xmdevops/simple_http_paser) 主要用于解析Socket Http Response, 对异步服务端粘包优雅处理,兼容PY2.7+

***


#### 开发环境:
> SY_ENV: MacOS 10.12.6 \
> PY_ENV: Python2.7.10 

***

#### 快速安装:
`git clone https://github.com/xmdevops/simple_http_paser` \
`cd simple_http_paser` \
`python setup.py install` 

***

#### 使用方法:
```python
#! -*- coding: utf-8 -*-


from agent.libs.simple_http_parser.http import HttpStream
from agent.libs.simple_http_parser.reader import SocketReader


def pack_post_data(uri, **kwargs):
    header_list = []
    for item in kwargs['headers'].iteritems():
        header_list.append('{0}: {1}'.format(item[0], item[1]))

    post_data = [
        '{0} {1} HTTP/1.1'.format(kwargs['method'], uri),
        '\r\n'.join(header_list),
        '\r\n{0}'.format(kwargs['body'])
    ]

    data = '\r\n'.join(post_data)

    return data


def unblock_mode_recv(sock, buffer_size=4096):
    r = SocketReader(sock)
    s = HttpStream(r)
    s.read(buffer_size=buffer_size)
    data = s.body.next()

    return data
```
***

#### Copyright:
2017.12.07  (c) Limanman <xmdevops@vip.qq.com>

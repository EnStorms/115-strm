[license]: /LICENSE
[license-badge]: https://img.shields.io/github/license/Akimio521/AutoFilm?style=flat-square&a=1
[prs]: https://github.com/uwang/115-strm
[prs-badge]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square
[issues]: https://github.com/uwang/115-strm/issues/new
[issues-badge]: https://img.shields.io/badge/Issues-welcome-brightgreen.svg?style=flat-square
[release]: https://github.com/uwang/115-strm/releases/latest
[release-badge]: https://img.shields.io/github/v/release/uwang/115-strm?style=flat-square
[docker]: https://hub.docker.com/r/uwang/115-strm
[docker-badge]: https://img.shields.io/docker/pulls/uwang/115-strm?color=%2348BB78&logo=docker&label=pulls

# 115-strm

[![license][license-badge]][license]
[![prs][prs-badge]][prs]
[![issues][issues-badge]][issues]
[![release][release-badge]][release]
[![docker][docker-badge]][docker]

使用 alist 的情况下，下载 115 网盘内的目录树文件，根据目录树自动生成 strm 文件。

生成的 strm 文件添加到 emby 可进行播放。infuse 添加 emby 正常使用，不会触发 115 风控。

原理：每3分钟（可根据定时任务配置）获取一次 115 网盘内的 `目录树.txt`，并生成（更新） strm 文件。
>PS: 由于 alist 默认有文件缓存 30 分钟后，所以115网盘内的目录树更新后，strm 文件可能在下一个整点更新，也可能在第二个整点更新，可将alist缓存过期时间设置改小，更新更快

镜像内置的定时任务配置为：`*/3 * * * * sleep $((RANDOM % 60)) && /app/main.py`。如果不满足要求可自行修改。

创建 `docker-compose.yml` 文件

```yml
services:
    alpine:
        image: ghcr.io/uwang/115-strm:latest
        container_name: alist-strm
        environment:
          - ALIST_HOST=192.168.1.100
          - ALIST_PORT=5244
          - ALIST_115_MOUNT_PATH=/115
          - ALIST_115_TREE_FILE=/目录树.txt
          - EXCLUDE_OPTION=1
          - UPDATE_EXISTING=0
          - DELETE_ABSENT=1
          - ALIST_115_TREE_FILE_FOR_GUEST=/115/目录树.txt
          - MEDIA_EXTENSIONS=mp3,flac,wav,aac,ogg,wma,alac,m4a,aiff,ape,dsf,dff,wv,pcm,tta,mp4,mkv,avi,mov,wmv,flv,webm,vob,mpg,mpeg,iso
          - TZ=Asia/Shanghai
        volumes:
            - '/path/to/strm:/data' # 修改为自己的存储路径
        restart: 'unless-stopped'
```

## 环境变量

### 环境变量1：alist 相关

- alist 里需要关闭签名。关闭签名需要在2个地方都关闭:
    1. 在管理-设置-全局-关闭签名所有。
    2. 在储存-挂载的储存-启用签名选择关闭

相关环境变量：

```env
ALIST_HOST=192.168.1.100       # alist 主机的 ip
ALIST_PORT=5244                # alist 主机的端口
ALIST_115_MOUNT_PATH=/115      # 115网盘在 alist 中的挂载路径：115

# 可选配置，用于探测目录树的 sha1 是否改变，需启用 guest 用户，并给 guest 用户 webdav 读取权限
ALIST_115_TREE_FILE_FOR_GUEST=/115/目录树.txt
```

### 环境变量2：115网盘相关

假设 115 网盘的目录结构如下：

```txt
.
├── 媒体库
└── 目录树.txt
```

<img src="./img/115.png" alt="115目录结构" width="230" height="100">

则 ALIST_115_TREE_FILE 填写 `/目录树.txt`，EXCLUDE_OPTION 填写 `1`

```env
ALIST_115_TREE_FILE=/目录树.txt  # 每次在115网盘根目录生成目录树文件，并将其改为固定名称：目录树
EXCLUDE_OPTION=1                # 可选配置，排除的目录，一级目录填 1
```

### 环境变量3：其他

```env
UPDATE_EXISTING=0 # 可选配置，是否更新已存在的 strm 文件。默认 0 不更新。0 不更新；1 更新
DELETE_ABSENT=1   # 可选配置，是否删除目录树中不存在的 strm 文件。默认 1 删除。0 不删除；1 删除

# 可选配置，自定义需要生成 strm 文件的文件后缀名，不需要的可以删除
MEDIA_EXTENSIONS=mp3,flac,wav,aac,ogg,wma,alac,m4a,aiff,ape,dsf,dff,wv,pcm,tta,mp4,mkv,avi,mov,wmv,flv,webm,vob,mpg,mpeg,iso
```

## 启动服务

确认上述环境变量后，启动服务：

```bash
docker compose up -d
```

## 文件后缀列表

常见媒体文件后缀：

- 音频文件格式：mp3,flac,wav,aac,ogg,wma,alac,m4a,aiff,ape,dsf,dff,wv,pcm,tta
- 视频文件格式：mp4,mkv,avi,mov,wmv,flv,webm,vob,mpg,mpeg
- 光盘镜像文件格式：iso

## Shell 脚本版

<https://github.com/suixing8/115-strm>

## 最后，转发请注明出处

感谢 [@suixing8](https://github.com/suixing8)

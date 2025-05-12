#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import urllib.parse
import requests
import chardet  # 用于检测文件编码
import json
from datetime import datetime
import hashlib

# 从环境变量获取配置
ALIST_URL = os.getenv("ALIST_HOST", "http://127.0.0.1")
ALIST_115_MOUNT_PATH = os.getenv("ALIST_115_MOUNT_PATH", "/115")
ALIST_115_TREE_FILE = os.getenv("ALIST_115_TREE_FILE", "/目录树.txt")
STRM_SAVE_PATH = os.getenv("STRM_SAVE_PATH", "/data")
EXCLUDE_OPTION = int(os.getenv("EXCLUDE_OPTION", 1))
UPDATE_EXISTING = int(os.getenv("UPDATE_EXISTING", 0)) # 是否更新已存在的 strm 文件，默认不更新
DELETE_ABSENT = int(os.getenv("DELETE_ABSENT", 1))     # 是否删除目录树中不存在的 strm 文件，默认删除

ALIST_115_TREE_FILE_FOR_GUEST = os.getenv("ALIST_115_TREE_FILE_FOR_GUEST", "")

ALIST_FILE_URL_PRFIX = f"{ALIST_URL}/d{ALIST_115_MOUNT_PATH}"
DIRECTORY_TREE_FILE = f"{ALIST_FILE_URL_PRFIX}{ALIST_115_TREE_FILE}"

def get_media_extensions():
    default_extensions = {
        "mp3", "flac", "wav", "aac", "ogg", "wma", "alac", "m4a",
        "aiff", "ape", "dsf", "dff", "wv", "pcm", "tta",
        "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "vob", "mpg", "mpeg",
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg", "heic",
        "iso", "img", "bin", "nrg", "cue", "dvd",
        "lrc", "srt", "sub", "ssa", "ass", "vtt", "txt",
        "pdf", "doc", "docx", "csv", "xml", "new"
    }
    env_extensions = os.getenv("MEDIA_EXTENSIONS", "")
    if env_extensions:
        return set(ext.strip() for ext in env_extensions.split(",") if ext.strip())
    return default_extensions

def extract_filename_from_url(url):
    parsed_url = urllib.parse.urlparse(url)
    return os.path.basename(parsed_url.path)

def get_file_sha1(file_path):
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha1.update(chunk)
        return sha1.hexdigest()
    except FileNotFoundError:
        print(f"文件不存在: {file_path}")
    except Exception as e:
        print(f"计算 SHA1 失败: {e}")
    return None

def fetch_file_info(api_url, file_path, page=1, per_page=0, refresh=True):
    payload = json.dumps({
        "path": file_path,
        "page": page,
        "per_page": per_page,
        "refresh": refresh
    })
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(api_url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def extract_modified_and_sha1(response_data):
    try:
        modified = response_data['data']['modified']
        sha1 = response_data['data']['hash_info']['sha1'].lower()
        formatted_modified = datetime.fromisoformat(modified).strftime("%Y-%m-%d %H:%M:%S")
        return formatted_modified, sha1
    except (KeyError, TypeError) as e:
        print(f"数据提取失败: {e}")
        return None, None

def download_with_redirects(url, output_file):
    print(f"下载目录树文件: {url}")
    try:
        headers = {
            "User-Agent": "curl/8.1.2",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "*/*",
        }
        response = requests.get(url, headers=headers, stream=True, allow_redirects=True)
        response.raise_for_status()
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"文件已下载并保存到: {output_file}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")

def detect_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def parse_directory_tree(file_path, generated_file):
    current_path_stack = []
    encoding = detect_file_encoding(file_path)
    print(f"检测到目录树文件编码: {encoding}")
    with open(file_path, 'r', encoding=encoding) as file, open(generated_file, 'w', encoding='utf-8') as output_file:
        for line in file:
            line = line.lstrip('﻿').strip()
            line_depth = line.count('|')
            item_name = line.split('|-')[-1].strip()
            if not item_name:
                continue
            while len(current_path_stack) > line_depth:
                current_path_stack.pop()
            if len(current_path_stack) == line_depth:
                if current_path_stack:
                    current_path_stack.pop()
            current_path_stack.append(item_name)
            full_path = '/' + '/'.join(current_path_stack)
            output_file.write(full_path + '\n')

def generate_strm_files(directory_file, strm_path, alist_full_url, exclude_option):
    os.makedirs(strm_path, exist_ok=True)
    media_extensions = get_media_extensions()
    generated_files = set()
    with open(directory_file, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.count('/') < exclude_option + 1:
                continue
            adjusted_path = '/'.join(line.split('/')[exclude_option + 1:])
            if adjusted_path.split('.')[-1].lower() in media_extensions:
                encoded_path = urllib.parse.quote(adjusted_path)
                full_url = f"{alist_full_url}/{encoded_path}"
                strm_file_path = os.path.join(strm_path, adjusted_path + '.strm')
                os.makedirs(os.path.dirname(strm_file_path), exist_ok=True)

                if os.path.exists(strm_file_path):
                    with open(strm_file_path, 'r', encoding='utf-8') as existing_file:
                        existing_content = existing_file.read().strip()
                    if existing_content == full_url:
                        generated_files.add(os.path.abspath(strm_file_path))
                        continue
                    elif UPDATE_EXISTING == 0:
                        generated_files.add(os.path.abspath(strm_file_path))
                        continue

                with open(strm_file_path, 'w', encoding='utf-8') as strm_file:
                    strm_file.write(full_url)
                generated_files.add(os.path.abspath(strm_file_path))
    return generated_files

def delete_absent_files(strm_path, generated_files):
    for root, _, files in os.walk(strm_path):
        for file in files:
            if file.endswith('.strm'):
                full_path = os.path.abspath(os.path.join(root, file))
                if full_path not in generated_files:
                    os.remove(full_path)
                    print(f"删除多余文件: {full_path}")

if __name__ == "__main__":
    if DIRECTORY_TREE_FILE.startswith("http"):
        output_file = f"{STRM_SAVE_PATH}/{extract_filename_from_url(DIRECTORY_TREE_FILE)}"
        if ALIST_115_TREE_FILE_FOR_GUEST:
            api_url_file_info = f"{ALIST_URL}/api/fs/get"
            response = fetch_file_info(api_url_file_info, ALIST_115_TREE_FILE_FOR_GUEST)
            if response:
                modified, sha1 = extract_modified_and_sha1(response)
                if modified is None and sha1 is None:
                    print("alist 无法获取文件，请检查115登录状态")
                    exit(1)
                elif os.path.isfile(output_file) and sha1 == get_file_sha1(output_file):
                    print(f"文件 hash 值未改变，更新跳过。 Modified: {modified} SHA1: {sha1}")
                    exit(1)
                else:
                    download_with_redirects(DIRECTORY_TREE_FILE, output_file)
        else:
            download_with_redirects(DIRECTORY_TREE_FILE, output_file)
    else:
        output_file = DIRECTORY_TREE_FILE

    if not os.path.isfile(output_file):
        print(f"目录树文件不存在: {output_file}")
        exit(1)

    converted_file = os.path.splitext(output_file)[0] + '_converted.txt'
    parse_directory_tree(output_file, converted_file)
    generated_files = generate_strm_files(converted_file, STRM_SAVE_PATH, ALIST_FILE_URL_PRFIX, EXCLUDE_OPTION)
    if DELETE_ABSENT == 1:
        delete_absent_files(STRM_SAVE_PATH, generated_files)
    os.remove(converted_file)
    print(".strm 文件生成完成！")

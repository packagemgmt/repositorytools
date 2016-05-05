#!/usr/bin/env bash

#set -e # can't use because of

FILE_SIZE_KB=10000

local_file=/tmp/foo-1.0.txt
repo_id=test
group=com.github.repositorytools

#echo foo > ${local_file}

dd if=/dev/urandom bs=1000 count=${FILE_SIZE_KB} of=${local_file}

/usr/bin/time -v artifact upload ${local_file} ${repo_id} ${group}
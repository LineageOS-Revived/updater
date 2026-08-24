#!/usr/bin/env python
from __future__ import print_function
import hashlib
import json
import logging
import os
import sys
from zipfile import ZipFile

from datetime import datetime
from time import mktime

if len(sys.argv) < 2:
    print("usage python {} /path/to/mirror/base/url".format(sys.argv[0]))
    sys.exit()

FILE_BASE = sys.argv[1]
builds = {}


def read_android_metadata(path, *keys):
    ret = [None] * len(keys)

    try:
        with ZipFile(path) as f:
            for line in f.read("META-INF/com/android/metadata").decode().splitlines():
                key, value = line.split("=", maxsplit=1)

                if key in keys:
                    ret[keys.index(key)] = value
    except:
        logging.warning(
            f"Failed to read META-INF/com/android/metadata for {path}", exc_info=True
        )

    return ret


for f in [os.path.join(dp, f) for dp, dn, fn in os.walk(FILE_BASE) for f in fn]:
    data = open(f, "rb")
    filename = f.split('/')[-1]
    # lineage-14.1-20171129-nightly-hiaeul-signed.zip
    _, version, builddate, buildtype, device, _ = os.path.splitext(filename)[0].split('-')
    ota_property_files, os_sdk_level, os_patch_level, timestamp = (
        read_android_metadata(
            f,
            "ota-property-files",
            "post-sdk-level",
            "post-security-patch-level",
            "post-timestamp",
        )
    )
    if os_sdk_level:
        os_sdk_level = int(os_sdk_level)

    if not timestamp:
        timestamp = int(mktime(datetime.strptime(builddate, "%Y%m%d").timetuple()))
    else:
        timestamp = int(timestamp)

    builds.setdefault(device, []).append(
        {
            "date": "{}-{}-{}".format(builddate[0:4], builddate[4:6], builddate[6:8]),
            "datetime": timestamp,
            "version": version,
            "type": buildtype,
            "ota_property_files": ota_property_files,
            "os_sdk_level": os_sdk_level,
            "os_patch_level": os_patch_level,
            "files": {
                "filepath": FILE_BASE,
                "filename": filename,
                "sha256": hashlib.file_digest(data, "sha256").hexdigest(),
                #"sha1": hashlib.file_digest(data, "sha1").hexdigest(),
                "size": os.path.getsize(f),
            }
        },
    )

for device in builds.keys():
    builds[device] = sorted(builds[device], key=lambda x: x['date'])
print(json.dumps(builds, sort_keys=True, indent=4))

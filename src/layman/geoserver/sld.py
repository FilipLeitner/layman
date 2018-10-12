import io
import json
import traceback

import requests
from urllib.parse import urljoin

from flask import g, current_app

from layman.filesystem.input_sld import get_layer_file
from layman.http import LaymanError

from . import headers_json
from layman.settings import *

FLASK_WFS_PROXY_KEY = 'layman.geoserver.wfs_proxy'

def update_layer(username, layername, layerinfo):
    pass


def delete_layer(username, layername):
    style_url = urljoin(LAYMAN_GS_REST_WORKSPACES,
                    username + '/styles/' + layername)
    try:
        r = requests.get(style_url + '.sld',
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        sld_file = io.BytesIO(r.content)

        r = requests.delete(style_url,
            headers=headers_json,
            auth=LAYMAN_GS_AUTH,
            params = {
                'purge': 'true',
                'recurse': 'true',
            }
        )
        r.raise_for_status()
        g.pop(FLASK_WFS_PROXY_KEY, None)
        return {
            'sld': {
                'file': sld_file
            }
        }
    except Exception:
        traceback.print_exc()
        pass
    return {}


def get_layer_info(username, layername):
    return {}


def get_layer_names(username):
    return []


def create_layer_style(username, layername):
    sld_file = get_layer_file(username, layername)
    # print('create_layer_style', sld_file)
    if sld_file is None:
        r = requests.get(
            urljoin(LAYMAN_GS_REST_STYLES, 'generic.sld'),
            auth=LAYMAN_GS_AUTH
        )
        r.raise_for_status()
        sld_file = io.BytesIO(r.content)
    r = requests.post(
        urljoin(LAYMAN_GS_REST_WORKSPACES, username + '/styles/'),
        data=json.dumps(
            {
                "style": {
                    "name": layername,
                    # "workspace": {
                    #     "name": "browser"
                    # },
                    "format": "sld",
                    # "languageVersion": {
                    #     "version": "1.0.0"
                    # },
                    "filename": layername + ".sld"
                }
            }
        ),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    r.raise_for_status()
    # app.logger.info(sld_file.read())
    r = requests.put(
        urljoin(LAYMAN_GS_REST_WORKSPACES, username +
                '/styles/' + layername),
        data=sld_file.read(),
        headers={
            'Accept': 'application/json',
            'Content-type': 'application/vnd.ogc.sld+xml',
        },
        auth=LAYMAN_GS_AUTH
    )
    if r.status_code == 400:
        raise LaymanError(14, data=r.text)
    r.raise_for_status()
    r = requests.put(
        urljoin(LAYMAN_GS_REST_WORKSPACES, username +
                '/layers/' + layername),
        data=json.dumps(
            {
                "layer": {
                    "defaultStyle": {
                        "name": username + ':' + layername,
                        "workspace": username,
                    },
                }
            }
        ),
        headers=headers_json,
        auth=LAYMAN_GS_AUTH
    )
    # app.logger.info(r.text)
    r.raise_for_status()
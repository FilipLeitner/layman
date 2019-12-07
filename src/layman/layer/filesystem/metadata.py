import os
import pathlib

from flask import url_for, current_app

from . import util
from . import input_file
from layman.common.metadata.util import fill_template


DIR = __name__.split('.')[-1]


def get_dir(username, layername):
    input_sld_dir = os.path.join(util.get_layer_dir(username, layername),
                                 DIR)
    return input_sld_dir


def ensure_dir(username, layername):
    input_sld_dir = get_dir(username, layername)
    pathlib.Path(input_sld_dir).mkdir(parents=True, exist_ok=True)
    return input_sld_dir


get_layer_info = input_file.get_layer_info


get_layer_names = input_file.get_layer_names


update_layer = input_file.update_layer


get_publication_names = input_file.get_publication_names


get_publication_uuid = input_file.get_publication_uuid


def delete_layer(username, layername):
    util.delete_layer_subdir(username, layername, DIR)


def get_file_path(username, layername):
    input_sld_dir = get_dir(username, layername)
    return os.path.join(input_sld_dir, layername+'.xml')


def save_file(username, layername, xml_file):
    xml_path = get_file_path(username, layername)
    if xml_file is None:
        delete_layer(username, layername)
    else:
        ensure_dir(username, layername)
        with open(xml_path, 'wb') as out:
            out.write(xml_file.read())


def get_file(username, layername):
    sld_path = get_file_path(username, layername)

    if os.path.exists(sld_path):
        return open(sld_path, 'rb')
    return None


def create_file(username, layername):
    template_values = _get_template_values(username=username, layername=layername)
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'metadata-template.xml')
    file_object = fill_template(template_path, template_values)
    save_file(username, layername, file_object)


def _get_template_values(
        uuid='ca238200-8200-1a23-9399-42c9fca53542',
        epsg_codes=None,
        title='CORINE - Krajinný pokryv CLC 90',
        date='2007-05-25',
        date_type='revision',
        data_identifier='http://www.env.cz/data/corine/1990',
        data_identifier_label='MZP-CORINE',
        abstract=None,
        username='browser',
        layername='layer',
        extent=None,
        ows_url="http://www.env.cz/corine/data/download.zip",
        scale_denominator=None,
        dataset_language=None,
):
    epsg_codes = epsg_codes or ['3857', '4326']
    extent = extent or [11.87, 19.13, 48.12, 51.59]

    result = {
        ###############################################################################################################
        # KNOWN TO LAYMAN
        ###############################################################################################################

        # layer UUID with prefix "m"
        'file_identifier': f"m{uuid}",

        'reference_system': ' '.join([
f"""
<gmd:referenceSystemInfo>
    <gmd:MD_ReferenceSystem>
        <gmd:referenceSystemIdentifier>
            <gmd:RS_Identifier>
                <gmd:code>
                    <gmx:Anchor xlink:href="http://www.opengis.net/def/crs/EPSG/0/{epsg_code}">EPSG:{epsg_code}</gmx:Anchor>
                </gmd:code>
            </gmd:RS_Identifier>
        </gmd:referenceSystemIdentifier>
    </gmd:MD_ReferenceSystem>
</gmd:referenceSystemInfo>
""" for epsg_code in epsg_codes
        ]),

        # title of data
        'title': title,

        # date of dataset
        # check GeoServer's REST API, consider revision or publication dateType
        'date': f"""
<gmd:CI_Date>
    <gmd:date>
        <gco:Date>{date}</gco:Date>
    </gmd:date>
    <gmd:dateType>
        <gmd:CI_DateTypeCode codeListValue="{date_type}" codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode">{date_type}</gmd:CI_DateTypeCode>
    </gmd:dateType>
</gmd:CI_Date>
""",

        # it must be URI, but text node is optional (MZP-CORINE)
        # it can point to Layman's Layer endpoint
        'data_identifier': f'<gmx:Anchor xlink:href="{data_identifier}">{data_identifier_label}</gmx:Anchor>',

        'abstract': '<gmd:abstract gco:nilReason="unknown" />' if abstract is None else f"""
<gmd:abstract>
    <gco:CharacterString>{abstract}</gco:CharacterString>
</gmd:abstract>
""",

        'graphic_url': url_for('rest_layer_thumbnail.get', username=username, layername=layername, _external=True),

        'extent': """
<gmd:EX_GeographicBoundingBox>
    <gmd:westBoundLongitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:westBoundLongitude>
    <gmd:eastBoundLongitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:eastBoundLongitude>
    <gmd:southBoundLatitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:southBoundLatitude>
    <gmd:northBoundLatitude>
        <gco:Decimal>{}</gco:Decimal>
    </gmd:northBoundLatitude>
</gmd:EX_GeographicBoundingBox>
""".format(*extent),

        'wms_url': ows_url,

        'wfs_url': ows_url,

        'layer_endpoint': url_for('rest_layer.get', username=username, layername=layername, _external=True),


        ###############################################################################################################
        # GUESSABLE BY LAYMAN
        ###############################################################################################################

        'scale_denominator': '<gmd:denominator gco:nilReason="unknown" />' if scale_denominator is None else f"""
<gmd:denominator>
    <gco:Integer>{scale_denominator}</gco:Integer>
</gmd:denominator>
""",

        # code for no language is "zxx"
        'dataset_language': '<gmd:language gco:nilReason="unknown" />' if dataset_language is None else f"""
<gmd:language>
    <gmd:LanguageCode codeListValue=\"{dataset_language}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{dataset_language}</gmd:LanguageCode>
</gmd:language>
""",

    }

    return result

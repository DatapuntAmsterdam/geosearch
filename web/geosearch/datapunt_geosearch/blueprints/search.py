# Python
import json

from flask import Blueprint, request, jsonify, current_app
from flask import send_from_directory

from datapunt_geosearch.datasource import AtlasDataSource
from datapunt_geosearch.datasource import BominslagMilieuDataSource
from datapunt_geosearch.datasource import MunitieMilieuDataSource
from datapunt_geosearch.datasource import NapMeetboutenDataSource
from datapunt_geosearch.datasource import TellusDataSource
from datapunt_geosearch.datasource import MonumentenDataSource

search = Blueprint('search', __name__)


def get_coords_and_type(args):
    """
    Retrieves the coordinates from the request and identifies if the request is
    in RD or in wgs84. If no coordinates are found an error message is set in a
    response dict. The RD flag is set to true if the coords given are in rd.

    @params
    args - The request args

    @Returns
    A tuple with the x, y, rd flag and response dict
    """
    resp = None
    rd = True

    x = args.get('x')
    y = args.get('y')
    limit = args.get('limit')

    if not x or not y:
        x = args.get('lat')
        y = args.get('lon')

        if x and y:
            rd = False
        else:
            resp = {'error': 'No coordinates found'}

    return x, y, rd, limit, resp


@search.route('/docs/geosearch.yml', methods=['GET', 'OPTIONS'])
def send_doc():
    return send_from_directory('static', 'geosearch.yml',
                               mimetype='application/x-yaml')


@search.route('/search/', methods=['GET', 'OPTIONS'])
def search_in_datasets():
    """
    General geosearch endpoint.
    Required arguments:
    x/y or lat/lon for position
    radius - search radius in meters
    item - Search item. adressen, meetbouten, kadastrale_objecten etc
    """
    x, y, rd, limit, resp = get_coords_and_type(request.args)
    # If no coords are given, there is a response error
    # message generated by get_coords_and_type. Returning
    # that message. Otherwise there are coords and it is
    # possible to continue
    if resp:
        return jsonify(resp)

    item = request.args.get('item')
    if not item:
        return jsonify({'error': 'No item type found'})

    # Got coords, radius and item. Time to search
    if item in ['peilmerk', 'meetbout']:
        ds = NapMeetboutenDataSource(dsn=current_app.config['DSN_NAP'])
    elif item in ['gevrijwaardgebied', 'uitgevoerdonderzoek',
                  'verdachtgebied']:
        ds = MunitieMilieuDataSource(dsn=current_app.config['DSN_MILIEU'])
    elif item == 'bominslag':
        ds = BominslagMilieuDataSource(dsn=current_app.config['DSN_MILIEU'])
    elif item == 'tellus':
        ds = TellusDataSource(dsn=current_app.config['DSN_TELLUS'])
    elif item == 'monument':
        ds = MonumentenDataSource(dsn=current_app.config['DSN_MONUMENTEN'])
    else:
        ds = AtlasDataSource(dsn=current_app.config['DSN_ATLAS'])

    # Checking for radius and item type
    radius = request.args.get('radius')
    if radius:
        ds.meta['operator'] = 'within'
    else:
        ds.meta['operator'] = 'contains'

    # Filtering to the required dataset
    known_dataset = ds.filter_dataset(item)
    if not known_dataset:
        return jsonify({'error': 'Unknown item type'})

    resp = ds.query(float(x), float(y), rd=rd, limit=limit, radius=radius)
    return jsonify(resp)


@search.route('/nap/', methods=['GET', 'OPTIONS'])
def search_geo_nap():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, limit, resp = get_coords_and_type(request.args)

    # If no error is found, query
    if not resp:
        ds = NapMeetboutenDataSource(dsn=current_app.config['DSN_NAP'])
        resp = ds.query(float(x), float(y), rd=rd, limit=limit,
                        radius=request.args.get('radius'))

    return jsonify(resp)


@search.route('/monumenten/', methods=['GET', 'OPTIONS'])
def search_geo_monumenten():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, limit, resp = get_coords_and_type(request.args)

    monumenttype = request.args.get('monumenttype')

    # If no error is found, query
    if not resp:
        ds = MonumentenDataSource(dsn=current_app.config['DSN_MONUMENTEN'])
        kwargs = {
            'rd':rd,
            'limit':limit,
            'radius':request.args.get('radius')
        }
        if monumenttype is not None:
            kwargs['monumenttype'] = monumenttype
        resp = ds.query(float(x), float(y), **kwargs)

    return jsonify(resp)


@search.route('/munitie/', methods=['GET', 'OPTIONS'])
def search_geo_munitie():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, limit, resp = get_coords_and_type(request.args)

    # If no error is found, query
    if not resp:
        ds = MunitieMilieuDataSource(dsn=current_app.config['DSN_MILIEU'])
        resp = ds.query(float(x), float(y), rd=rd, limit=limit)

    return jsonify(resp)


@search.route('/bominslag/', methods=['GET', 'OPTIONS'])
def search_geo_bominslag():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, limit, resp = get_coords_and_type(request.args)

    # If no error is found, query
    if not resp:
        ds = BominslagMilieuDataSource(dsn=current_app.config['DSN_MILIEU'])
        resp = ds.query(float(x), float(y), rd=rd, limit=limit,
                        radius=request.args.get('radius'))

    return jsonify(resp)


@search.route('/atlas/', methods=['GET', 'OPTIONS'])
def search_geo_atlas():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, limit, resp = get_coords_and_type(request.args)

    # If no error is found, query
    if not resp:
        ds = AtlasDataSource(dsn=current_app.config['DSN_ATLAS'])
        resp = ds.query(float(x), float(y), rd=rd, limit=limit)

    return jsonify(resp)


# Adding cors headers
@search.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add(
        'Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

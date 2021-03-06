# Packages
import time
import json
from flask import Blueprint, Response, current_app

from datapunt_geosearch.datasource import BagDataSource, \
    NapMeetboutenDataSource
from datapunt_geosearch.registry import registry

health = Blueprint('health', __name__)


@health.route('/status', methods=['GET', 'HEAD', 'OPTIONS'])
def system_status():
    message = json.dumps({
        "Delay": registry.INITIALIZE_DELAY,
        "Datasets initialized": registry._datasets_initialized,
        "Time since last refresh": time.time() - (registry._datasets_initialized or time.time())
    })
    return Response(message,
                    content_type='application/json')


@health.route('/status/force-refresh', methods=['GET', 'HEAD', 'OPTIONS'])
def force_refresh():
    registry._datasets_initialized = time.time()
    registry.init_datasets()
    return system_status()


@health.route('/status/health', methods=['GET', 'HEAD', 'OPTIONS'])
def search_list():
    """Execute test query against datasources"""
    x, y, response_text = 120993, 485919, []
    # Trying to load the data sources
    try:
        bag_dsn = BagDataSource(dsn=current_app.config['DSN_BAG'])
        nap_dsn = NapMeetboutenDataSource(dsn=current_app.config['DSN_NAP'])
    except Exception as e:
        return repr(e), 500
    # Attempting to query
    try:
        results = bag_dsn.query(x, y)
    except Exception as e:
        return repr(e), 500

    if results['type'] == 'Error':
        return Response(results['message'],
                        content_type='text/plain; charset=utf-8',
                        status=500)

    if not len(results['features']):
        response_text.append('No results from bag dataset')

    results = nap_dsn.query(x, y)

    if not len(results['features']):
        response_text.append('No results from nap/meetbouten dataset')

    if not len(response_text):
        return Response(' - '.join(response_text),
                        content_type='text/plain; charset=utf-8',
                        status=500)

    return Response("Connectivity OK",
                    content_type='text/plain; charset=utf-8')

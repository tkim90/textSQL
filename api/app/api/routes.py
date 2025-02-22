from flask import Blueprint, jsonify, make_response, request
from .utils import text_to_sql_with_retry, text_to_sql_parallel
from .lat_lon import zip_lat_lon
from sentry_sdk import capture_exception


bp = Blueprint('api_bp', __name__)


@bp.route('/text_to_sql', methods=['POST'])
def text_to_sql():
    """
    Convert natural language query to SQL
    """
    request_body = request.get_json()
    natural_language_query = request_body.get('natural_language_query')

    if not natural_language_query:
        error_msg = 'natural_language_query is missing from request body'
        return make_response(jsonify({'error': error_msg}), 400)

    try:
        # LM outputs are non-deterministic, so same natural language query may result in different SQL queries (some of which may be invalid)
        # Generate queries in parallel and use the first one that works
        # result, sql_query, messages = text_to_sql_parallel(natural_language_query)
        # if result is None or sql_query is None:
        #     result, sql_query = text_to_sql_with_retry(natural_language_query, messages=messages)
        result, sql_query = text_to_sql_with_retry(natural_language_query)
    except Exception as e:
        capture_exception(e)
        error_msg = f'Error processing request: {str(e)}'
        return make_response(jsonify({'error': error_msg}), 500)

    return make_response(jsonify({'result': result, 'sql_query': sql_query}), 200)


@bp.route('/zip_to_lat_lon', methods=['GET'])
def zip_to_lat_lon():
    """
    Get lat/lon coordinates for a zip code
    """
    zip_code = request.args.get('zip_code')

    if not zip_code:
        error_msg = 'zip_code is missing from request parameters'
        return make_response(jsonify({'error': error_msg}), 400)

    try:
        lat = zip_lat_lon[zip_code]['lat']
        lon = zip_lat_lon[zip_code]['lon']
    except KeyError as e:
        capture_exception(e)
        error_msg = f'Invalid zip_code: {zip_code}'
        return make_response(jsonify({'error': error_msg}), 400)

    return make_response(jsonify({'lat': lat, 'lon': lon}), 200)
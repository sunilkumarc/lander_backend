import json
import uuid
from basicauth.decorators import basic_auth_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging as logger
from lander_backend.constants import *
from website.website import *

def send_json_response(code, message):
    return HttpResponse(json.dumps(message), status=code, content_type="application/json")

@basic_auth_required
@require_http_methods(["GET", "POST"])
@csrf_exempt
def website(request):
    u = str(uuid.uuid4())
    if request.method == "POST":
        log_identifier = CREATE_WEBSITE + ":" + UUID + ":" + u + ":"
        body = json.loads(request.body)
        website_details = None

        try:
            website_details = create_website_from_template(body, log_identifier)
        except Exception as e:
            logger.error(log_identifier + "Exception occurred when creating website: {}".format(e))
            return send_json_response(500, dict(success=False, uuid=u, error=str(e)))

        return send_json_response(200, dict(success=True, uuid=u, website_details=website_details))

    elif request.method == "GET":
        website_name = request.GET.get('website_name', None)
        if not website_name:
            return send_json_response(400, dict(success=False, uuid=u, error="website_name parameter is mandatory"))

        log_identifier = GET_WEBSITE_DETAILS_BY_NAME + ":" + UUID + ":" + u + ":"
        try:
            website_details = get_website_details(website_name, log_identifier)
            if not website_details:
                return send_json_response(204, dict(success=True, uuid=u, website_details={}))
        except Exception as e:
            logger.error(log_identifier + "Exception occurred when getting website details: {}".format(e))
            return send_json_response(500, dict(success=False, uuid=u, error=str(e)))

        return send_json_response(200, dict(success=True, uuid=u, website_details=json.loads(website_details)))

@basic_auth_required
@require_http_methods(["GET", "POST"])
@csrf_exempt
def website_session(request):
    u = str(uuid.uuid4())
    if request.method == "POST":
        log_identifier = CREATE_WEBSITE_SESSION + ":" + UUID + ":" + u + ":"
        body = json.loads(request.body)

        try:
            website_details = create_website_session_details(body, u, log_identifier)
        except Exception as e:
            logger.error(log_identifier + "Exception occurred when creating website: {}".format(e))
            return send_json_response(500, dict(success=False, uuid=u, error=str(e)))

        return send_json_response(200, dict(success=True, uuid=u, website_details=json.loads(website_details)))

    elif request.method == "GET":
        website_uuid = request.GET.get('uuid', None)
        if not website_uuid:
            return send_json_response(400, dict(success=False, uuid=u, error="website_uuid parameter is mandatory"))

        log_identifier = GET_WEBSITE_SESSION_DETAILS_BY_UUID + ":" + UUID + ":" + u + ":"
        try:
            website_session_details = get_website_session_details(website_uuid, log_identifier)
            if not website_session_details:
                return send_json_response(204, dict(success=True, uuid=u, website_details={}))
        except Exception as e:
            logger.error(log_identifier + "Exception occurred when getting website details: {}".format(e))
            return send_json_response(500, dict(success=False, uuid=u, error=str(e)))

        return send_json_response(200, dict(success=True, uuid=u, website_details=json.loads(website_session_details)))
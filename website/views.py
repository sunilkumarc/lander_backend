import json
import uuid
from basicauth.decorators import basic_auth_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging as logger
from lander_backend.constants import *
from website.website import create_website_from_template

def send_json_response(code, message):
    return HttpResponse(json.dumps(message), status=code, content_type="application/json")

@basic_auth_required
@require_http_methods(["POST"])
@csrf_exempt
def create_website(request):
    u = str(uuid.uuid4())
    log_identifier = CREATE_WEBSITE + ":" + UUID + ":" + u + ":"
    body = json.loads(request.body)
    website_details = None

    try:
        website_details = create_website_from_template(body, log_identifier)
    except Exception as e:
        logger.error(log_identifier + "Exception occurred when creating website: {}".format(e))
        return send_json_response(500, dict(success=False, uuid=u, error=str(e)))

    return send_json_response(200, dict(success=True, uuid=u, website_details=website_details))
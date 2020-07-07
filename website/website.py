from website.models import Website
import tempfile, shutil, os
from django.contrib.staticfiles import finders
from django.core.exceptions import ObjectDoesNotExist
import zipfile
from django.conf import settings
from github import Github, GithubException
from django.template import Context, Template
from website.db import db_client
import json
from bson import ObjectId
from website.stripe import *
from website.exceptions import *
from website.helper import *
from lander_backend.constants import *

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def store_website_details(website_session_details):
    try:
        new_website = {
            "website_uuid": website_session_details["uuid"],
            "website_name": website_session_details["website_name"],
            "company_name": website_session_details["company_name"],
            "created_at": get_current_utc_timestamp(),
            "updated_at": get_current_utc_timestamp()
        }
        websites_collection = db_client.website
        website = websites_collection.insert_one(new_website)
        print("Website details stored successfully! Id: {}".format(website.inserted_id))

    except Exception as e:
        print("Exception occurred when saving website details: {}".format(e))

def website_already_exists(website_name):
    print("Checking if website {} already exists".format(website_name))
    try:
        websites_collection = db_client.website
        website = websites_collection.find_one({"website_name": website_name})
        if website:
            return True
    except ObjectDoesNotExist:
        print("Website {} doesn't exist".format(website_name))
        return False
    except Exception as e:
        print("Exception occurred when getting website by name: {}".format(e))
        raise e

    return False

def get_file_data_with_context(request, file_path):
    try:
        context = request
        if request["template_id"] == 2:
            feature_sections = request["feature_sections"]
            feature_sections_split = []

            for i in range(0, len(feature_sections), 3):
                each_row = feature_sections[i:i + 3]
                feature_sections_split.append(each_row)
            context["feature_sections"] = feature_sections_split

        with open(file_path, 'r') as f:
            data = f.read()
            t = Template(data)
            c = Context(context)
            html = t.render(c)
            return html
    except Exception as e:
        raise e

def create_github_repository_with_contents(request, extracted_template_folder):
    try:
        # github_client = Github(settings.GITHUB_OAUTH_TOKEN)
        github_client = Github("landrpage", "G63MEBrBxF7FwTT")
        user = github_client.get_user()
        repo_name = request["website_name"]
        created_repo = user.create_repo(repo_name)
        print("Created github repository with name {} successfully!".format(repo_name))

        for subdir, dirs, files in os.walk(extracted_template_folder):
            for file in files:
                file_path = os.path.join(subdir, file)

                if "__MACOSX" in file_path:
                    continue
                if ".DS_Store" in file_path:
                    continue
                repo_file_path = file_path.split(extracted_template_folder+"/")[1]
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                        if repo_file_path == "index.html":
                            data = get_file_data_with_context(request, file_path)

                        created_repo.create_file(repo_file_path, "Committing file " + repo_file_path, data, branch="gh-pages")
                        print("Committed file {} successfully".format(f.name))
                except Exception as e:
                    print("Could not commit file: {}, error: {}".format(f.name, e))
    except Exception as e:
        print("Exception occurred in create_github_repository_with_contents: {}".format(e))
        raise e

def extra_template_into_temp_dir(request):
    try:
        # 1. Check if website already exists with the give name
        exists = website_already_exists(request["website_name"])
        if exists:
            raise Exception("Website {} already exists".format(request["website_name"]))

        # 2. Copy template zip file to temporary location.
        template_id = str(request["template_id"])
        template_path = finders.find(template_id + ".zip")

        temp_dir = tempfile.gettempdir()
        if not os.path.exists(temp_dir + '/lander-templates'):
            os.makedirs(temp_dir + '/lander-templates')

        copied_template_zip_path = os.path.join(temp_dir + '/lander-templates', template_id + ".zip")
        shutil.copy2(template_path, copied_template_zip_path)
        print("Copied template {} to temporary location {}".format(template_path, copied_template_zip_path))

        # 3. Unzip the template file
        extracted_template_folder = temp_dir + '/lander-templates/' + template_id
        with zipfile.ZipFile(copied_template_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_template_folder)

        return extracted_template_folder
    except Exception as e:
        raise e

def create_website_on_github(website_session_details):
    try:
        extracted_template_folder = extra_template_into_temp_dir(website_session_details)
        create_github_repository_with_contents(website_session_details, extracted_template_folder)
        store_website_details(website_session_details)
    except Exception as e:
        raise e

def create_website_from_template(request, log_identifier):
    print(log_identifier+"Creating website with details: {}".format(request))
    try:
        website_uuid = request.get("website_uuid", "")
        stripe_session_id = request.get("stripe_session_id", "")
        if not website_uuid or not stripe_session_id:
            print(log_identifier+"website_uuid or stripe_session_id are missing")
            raise ErrorCreatingWebsiteException("website_uuid and stripe_session_id are mandatory parameters")

        website_session_collection = db_client.website_session
        website_session_details = website_session_collection.find_one({"uuid": website_uuid})
        print(log_identifier + "Extracted website session details {}".format(website_session_details))

        if stripe_session_id != website_session_details["stripe_session_id"]:
            print(log_identifier + "The stripe session id sent ({}) does not match the one in the database ({})".format(stripe_session_id, website_session_details["stripe_session_id"]))
            raise ErrorCreatingWebsiteException("The stripe session id sent ({}) does not match the one in the database ({})".format(stripe_session_id, website_session_details["stripe_session_id"]))

        payment_intent = get_stripe_payment_intent(website_session_details["payment_intent_id"], log_identifier)
        if payment_intent.amount_received != (STANDARD_WEBSITE_PRICE_IN_DOLLARS * 100):
            print(log_identifier + "Payment is not completed for website with uuid: {}".format(website_uuid))
            raise ErrorCreatingWebsiteException("Payment is not completed for website with uuid: {}".format(website_uuid))

        create_website_on_github(website_session_details)
        request["website_name"] = website_session_details["website_name"]
        request["website_url"] = LANDER_WEBSITE_HOST + "/" +  website_session_details["website_name"]
        request["payment_amount"] = payment_intent.amount_received / 100
        del request["stripe_session_id"]
    except Exception as e:
        print("Exception occurred when creating website: {}".format(e))
        raise e

    return request

def get_website_details(website_name, log_identifier):
    print(log_identifier+"Getting website details with name: {}".format(website_name))
    website_details = None
    try:
        websites_collection = db_client.website
        website_details = websites_collection.find_one({"website_name": website_name})

        if website_details:
            website_details = JSONEncoder().encode(website_details)
    except Exception as e:
        raise e
    return website_details

def create_website_session_details(website_session_details, u, log_identifier):
    print(log_identifier+"Creating website session details with uuid: {}".format(u))
    try:
        stripe_session = create_stripe_session_for_payment(website_session_details, u, log_identifier)
        website_session_details["stripe_session_id"] = stripe_session.id
        website_session_details["payment_intent_id"] = stripe_session.payment_intent
        website_session_details["created_at"] = get_current_utc_timestamp()
        website_session_details["updated_at"] = get_current_utc_timestamp()
        website_session_details["uuid"] = u

        websites_collection = db_client.website_session
        website_session = websites_collection.insert_one(website_session_details)
        print("Website session details stored successfully! id: {}".format(website_session.inserted_id))
        return JSONEncoder().encode(website_session_details)
    except Exception as e:
        raise e

def get_website_session_details(website_uuid, log_identifier):
    print(log_identifier+"Getting website details with uuid: {}".format(website_uuid))
    website_session_details = None
    try:
        website_session_collection = db_client.website_session
        website_session_details = website_session_collection.find_one({"uuid": website_uuid})
        if website_session_details:
            website_session_details = JSONEncoder().encode(website_session_details)
    except Exception as e:
        raise e
    return website_session_details
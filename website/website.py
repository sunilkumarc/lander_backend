import logging as logger
from website.models import Website
import tempfile, shutil, os
from django.contrib.staticfiles import finders
from django.core.exceptions import ObjectDoesNotExist
import zipfile
from django.conf import settings
from github import Github, GithubException
from django.template import Context, Template
from website.db import db_client

def store_website_details(body):
    try:
        new_website = {
            "website_name": body["website_name"],
            "company_name": body["company_name"],
            "template_id": body["template_id"],
            "plan": body["plan"],
            "payment_amount": body["payment_amount"]
        }
        websites_collection = db_client.website_website
        website = websites_collection.insert_one(new_website)
        print("Website details stored successfully! Id: {}".format(website.inserted_id))

    except Exception as e:
        print("Exception occurred when saving website details: {}".format(e))

def website_already_exists(website_name):
    print("Checking if website {} already exists".format(website_name))
    try:
        websites_collection = db_client.website_website
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
        feature_sections = request["feature_sections"]
        feature_sections_split = []

        for i in range(0, len(feature_sections), 3):
            each_row = feature_sections[i:i+3]
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
        github_client = Github(settings.GITHUB_OAUTH_TOKEN)
        user = github_client.get_user()
        repo_name = request["website_name"]
        created_repo = user.create_repo(repo_name)
        # created_repo = user.get_repo(repo_name)
        print("Created github repository with name {} successfully!".format(repo_name))

        for subdir, dirs, files in os.walk(extracted_template_folder):
            for file in files:
                file_path = os.path.join(subdir, file)
                if "__MACOSX" in file_path:
                    continue
                repo_file_path = file_path.split(extracted_template_folder+"/")[1]
                with open(file_path, 'r') as f:
                    data = f.read()
                    if repo_file_path == "index.html":
                        data = get_file_data_with_context(request, file_path)

                    created_repo.create_file(repo_file_path, "Committing file " + repo_file_path, data, branch="gh-pages")
                    print("Committed file {} successfully".format(f.name))

    except GithubException as ge:
        raise Exception(ge.data["message"])
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

def create_website_on_github(request):
    try:
        extracted_template_folder = extra_template_into_temp_dir(request)
        create_github_repository_with_contents(request, extracted_template_folder)
        store_website_details(request)
    except Exception as e:
        raise e

def create_website_from_template(request, log_identifier):
    logger.info(log_identifier+"Creating website with details: {}".format(request))

    try:
        create_website_on_github(request)
    except Exception as e:
        print("Exception occurred when creating website: {}".format(e))
        raise e

    return request
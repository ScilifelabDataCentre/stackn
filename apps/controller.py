import json
import os
import subprocess
import tarfile
import uuid

import yaml
from django.conf import settings

from .models import Apps

KUBEPATH = settings.KUBECONFIG


def delete(options):
    print("DELETE FROM CONTROLLER")
    # building args for the equivalent of helm uninstall command
    args = ["helm", "-n", options["namespace"], "delete", options["release"]]
    result = subprocess.run(args, capture_output=True)
    return result


def deploy(options):
    print("STARTING DEPLOY FROM CONTROLLER")

    if "ghcr" in options["chart"]:
        version = options["chart"].split(":")[-1]
        chart = "oci://" + options["chart"].split(":")[0]
    else:
        version = None
        chart = "charts/" + options["chart"]

    if "release" not in options:
        print("Release option not specified.")
        return json.dumps({"status": "failed", "reason": "Option release not set."})
    if "appconfig" in options:
        # check if path is root path
        if "path" in options["appconfig"]:
            if "/" == options["appconfig"]["path"]:
                print("Root path cannot be copied.")
                return json.dumps({"status": "failed", "reason": "Cannot copy / root path."})
        # check if valid userid
        if "userid" in options["appconfig"]:
            try:
                userid = int(options["appconfig"]["userid"])
            except Exception as ex:
                print("Userid not a number.")
                print(ex)
                return json.dumps({"status": "failed", "reason": "Userid not an integer."})
            if userid > 1010 or userid < 999:
                print("Userid outside of allowed range.")
                return json.dumps({"status": "failed", "reason": "Userid outside of allowed range."})
        else:
            # if no userid, then add default id of 1000
            options["appconfig"]["userid"] = "1000"
        # check if valid port
        if "port" in options["appconfig"]:
            try:
                port = int(options["appconfig"]["port"])
            except Exception as ex:
                print("Userid not a number.")
                print(ex)
                return json.dumps({"status": "failed", "reason": "Port not an integer."})
            if port > 9999 or port < 3000:
                print("Port outside of allowed range.")
                return json.dumps({"status": "failed", "reason": "Port outside of allowed range."})

    # Save helm values file for internal reference
    unique_filename = "charts/values/{}-{}.yaml".format(str(uuid.uuid4()), str(options["app_name"]))
    f = open(unique_filename, "w")
    f.write(yaml.dump(options))
    f.close()

    # building args for the equivalent of helm install command
    args = [
        "helm",
        "upgrade",
        "--install",
        "-n",
        options["namespace"],
        options["release"],
        chart,
        "-f",
        unique_filename,
    ]
    # Append version if deploying via ghcr
    if version:
        args.append("--version")
        args.append(version)
        args.append("--repository-cache"),
        args.append("/app/charts/.cache/helm/repository")

    print("CONTROLLER: RUNNING HELM COMMAND... ")
    result = subprocess.run(args, capture_output=True)

    # remove file
    rm_args = ["rm", unique_filename]
    subprocess.run(rm_args)

    return result

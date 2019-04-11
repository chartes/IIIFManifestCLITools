import copy
import json

import requests


def load_json(path):
    with open(path, 'r') as f:
        tmp = json.load(f)
    return tmp


def render_template(template, canvas, image, meta, manifest_url_prefix, image_url_prefix):
    tmp = copy.deepcopy(template)
    manifest_id = meta["manifest"]["id"]

    tmp["@id"] = "{0}/manifest_{1}.json".format(manifest_url_prefix, manifest_id)
    tmp["attribution"] = meta["metadata"]["attribution"]
    tmp["label"] = meta["manifest"]["label"]
    tmp["thumbnail"]["@id"] = image_url_prefix + "/" + meta["manifest"]["images"][0].replace("/full/full/", "/full/180,/")

    tmp["sequences"][0]["@id"] = "{0}/{1}/sequence/normal".format(manifest_url_prefix, manifest_id)
    # render canvases
    for i, img in enumerate(meta["manifest"]["images"]):
        img = image_url_prefix + "/" + img
        cv = copy.deepcopy(canvas)
        cv["label"] = meta["manifest"]["label"]
        cv["@id"] = "{0}/{1}/canvas/f{2}".format(manifest_url_prefix, manifest_id, i)
        img_tmp = copy.deepcopy(image)
        img_tmp["on"] = cv["@id"]
        img_tmp["@id"] = img
        img_tmp["resource"]["@id"] = img
        img_tmp["resource"]["service"]["@id"] = img.replace("/full/full/0/default.jpg", "")
        cv["images"].append(img_tmp)

        resp = requests.get(img_tmp["resource"]["service"]["@id"] + "/info.json")
        if resp.status_code != 404:
            resp = resp.json()
            cv["height"] = resp["height"]
            cv["width"] = resp["width"]

        tmp["sequences"][0]["canvases"].append(cv)

    return tmp


def render_collection(template, manifests):
    coll = copy.deepcopy(template)
    for m in manifests:
        coll["manifests"].append({
            "@id": m["@id"],
            "@type": "sc:Manifest",
            "label": m["label"]
        })
    return coll



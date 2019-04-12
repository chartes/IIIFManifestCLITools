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

    tmp["@id"] = "{0}/manifest{1}.json".format(manifest_url_prefix, manifest_id)
    tmp["attribution"] = meta["metadata"]["attribution"]
    tmp["label"] = meta["manifest"]["label"]

    tmp["sequences"][0]["@id"] = "{0}/{1}/sequence/normal".format(manifest_url_prefix, manifest_id)
    # render canvases
    for i, img in enumerate(meta["manifest"]["images"]):
        img = image_url_prefix + "/" + img
        cv = copy.deepcopy(canvas)
        cv["label"] = "p{0}".format(i+1)
        cv["@id"] = "{0}/{1}/canvas/f{2}".format(manifest_url_prefix, manifest_id, i+1)
        img_tmp = copy.deepcopy(image)
        img_tmp["on"] = cv["@id"]
        img_tmp["@id"] = "{0}/{1}/annotation/a{2}".format(manifest_url_prefix, manifest_id, i + 1)
        img_tmp["resource"]["@id"] = img
        img_tmp["resource"]["service"]["@id"] = img.replace("/full/full/0/default.jpg", "")
        cv["images"].append(img_tmp)

        resp = requests.get(img_tmp["resource"]["service"]["@id"] + "/info.json")
        if resp.status_code != 404:
            resp = resp.json()
            cv["height"] = resp["height"]
            cv["width"] = resp["width"]
            cv["thumbnail"] = {
              "@id": image_url_prefix + "/" + meta["manifest"]["images"][i].replace("/full/full/", "/full/180,/"),
              "@type":"dctypes:Image"
            }
        tmp["sequences"][0]["canvases"].append(cv)

    tmp["thumbnail"] = {
        "@id": tmp["sequences"][0]["canvases"][0]["@id"]
    }
    tmp["sequences"][0]["thumbnail"] = tmp["thumbnail"]

    return tmp


def render_collection(template, items, name, item_type="sc:Manifest"):
    coll = copy.deepcopy(template)
    t = "manifests" if item_type == "sc:Manifest" else "collections"
    coll[t] = []
    coll["@id"] = name
    for item in sorted(items, key=lambda e: e["@id"]):
        coll[t].append({
            "@id": item["@id"],
            "@type": item_type,
            "label": item["label"]
        })
    return coll



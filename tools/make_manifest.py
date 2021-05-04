import copy
import json

import requests


def load_json(path):
    with open(path, 'r') as f:
        tmp = json.load(f)
    return tmp

#Ajouter une séparation en deux fonctions pour créer le canvas globale et une autre partie les images ou ajouter dans cette fonction l'ajout des metadonnées
def render_template(template, canvas, annotation, image, meta, manifest_url_prefix, image_url_prefix, collection_url_prefix, dts_collection_url_prefix, dts_document_url_prefix, document_website_url_prefix):
    tmp = copy.deepcopy(template)
    manifest_id = meta["manifest"]["id"]

    # réécrire les chemins après maj de la logique de redirection
    tmp["id"] = "{0}/{1}.json".format(manifest_url_prefix, manifest_id)
    #A reprendre en envoyant le label en meta
    tmp["label"] = {"fr": [meta["manifest"]["label"]]}
    tmp["homepage"][0]["id"] = "{0}{1}".format(document_website_url_prefix, manifest_id)
    tmp["homepage"][0]["label"] = {"fr": ["Consultation de {0}".format(manifest_id)]}
    tmp["seeAlso"][0]["id"] = "{0}{1}".format(dts_collection_url_prefix, manifest_id)
    tmp["rendering"][0]["id"] = "{0}{1}".format(dts_document_url_prefix, manifest_id)
    tmp["partOf"][0]["id"] = "{0}{1}".format(collection_url_prefix, meta["collection"])


    # render canvases
    for i, img in enumerate(meta["manifest"]["images"]):
        #réécrire les prefix d'url
        img = image_url_prefix + "/" + img
        cv = copy.deepcopy(canvas)
        cv["label"] = {'none': ["p{0}".format(i+1)]}
        # réécrire les chemins après maj de la logique de redirection et selon les spécifités de chaque projet donc créer un fichier de configuration pour ces entrées
        cv["id"] = "{0}/{1}/canvas/f{2}".format(manifest_url_prefix, manifest_id, i+1)
        an = copy.deepcopy(annotation)
        #Mettre le annotation-page final selon le projet
        an["id"] = "{0}/{1}/annotation-page/p{2}".format(manifest_url_prefix, manifest_id, i+1)
        img_tmp = copy.deepcopy(image)
        img_tmp["on"] = cv["id"]
        # réécrire les chemins après maj de la logique de redirection
        img_tmp["id"] = "{0}/{1}/annotation/a{2}".format(manifest_url_prefix, manifest_id, i + 1)
        img_tmp["target"] = "{0}/{1}/canvas/f{2}".format(manifest_url_prefix, manifest_id, i + 1)
        img_tmp["body"]["id"] = img
        img_tmp["body"]["service"][0]["id"] = img.replace("/full/full/0/default.jpg", "")
        an["items"].append(img_tmp)
        cv["items"].append(an)

        resp = requests.get(img_tmp["body"]["service"][0]["id"] + "/info.json")
        if resp.status_code != 404:
            resp = resp.json()
            cv["height"] = resp["height"]
            cv["width"] = resp["width"]
        tmp["items"].append(cv)
        # configuration du thumbnail global sur la première image
        if tmp["thumbnail"][0]["id"] == "":
            tmp["start"]["id"] = tmp["items"][0]["id"]
            tmp["thumbnail"][0]["id"] = image_url_prefix + "/" + meta["manifest"]["images"][i].replace("/full/full/",
                                                                                                       "/full/180,/")
            tmp["thumbnail"][0]["service"][0]["id"] = img.replace("/full/full/0/default.jpg", "")
    print(tmp)
    print(tmp["thumbnail"][0]["id"])
    return tmp


def render_collection(template, items, name, item_type="Manifest"):
    coll = copy.deepcopy(template)
    t = "manifests" if item_type == "Manifest" else "collections"
    coll[t] = []
    coll["id"] = name
    for item in sorted(items, key=lambda e: e["id"]):
        coll[t].append({
            "id": item["id"],
            "type": item_type,
            "label": {"fr": item["label"]}
        })
    return coll



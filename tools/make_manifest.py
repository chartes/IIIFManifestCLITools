import copy
import json

import requests


def load_json(path):
    with open(path, 'r') as f:
        tmp = json.load(f)
    return tmp

#Ajouter une séparation en deux fonctions pour créer le canvas globale et une autre partie les images ou ajouter dans cette fonction l'ajout des metadonnées
def render_template(template, canvas, annotation, image, meta, manifest_url_prefix, image_url_prefix, first_page=1):
    tmp = copy.deepcopy(template)
    manifest_id = meta["manifest"]["id"]

    # render canvases
    for i, img in enumerate(meta["manifest"]["images"]):
        #réécrire les prefix d'url
        img = image_url_prefix + "/" + img
        cv = copy.deepcopy(canvas)
        if type(first_page) is list:
            cv["label"] = {'none': ["{0}".format(first_page[i])]}
        else:
            cv["label"] = {'none': ["p. {0}".format(i + first_page)]}
        # réécrire les chemins après maj de la logique de redirection et selon les spécifités de chaque projet donc créer un fichier de configuration pour ces entrées
        cv["id"] = "{0}/{1}/canvas/f{2}".format(manifest_url_prefix, manifest_id, i + 1)
        an = copy.deepcopy(annotation)
        #Mettre le annotation-page final selon le projet
        an["id"] = "{0}/{1}/annotation-page/p{2}".format(manifest_url_prefix, manifest_id, i + 1)
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
    return tmp


def render_collection(template, items, id, label, summary, thumbnail, item_type="Manifest"):
    coll = copy.deepcopy(template)
    t = "items"
    coll[t] = []
    coll["id"] = id
    #Ajouter une manière élégante de rajouter le label qui dépend entre le top et les sous collections
    coll["label"] = label
    coll["summary"] = summary
    if thumbnail != '':
        coll["thumbnail"][0]["id"] = thumbnail
        coll["thumbnail"][0]["service"][0]["id"] = thumbnail.split("/full")[0]
    if "top" in id:
       coll.pop("partOf")
    for item in items:
        coll[t].append({
            "id": item["id"],
            "type": item_type,
            "label": item["label"],
            "thumbnail": item["thumbnail"]
        })
    return coll



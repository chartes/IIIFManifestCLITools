import json
import os
import pprint
import re
import csv
import copy

from tools.make_manifest import load_json, render_template, render_collection

#INFOS
COLLECTION_NAME = "lasteyrie"

# TEMPLATES
METADATA = "meta/{0}/metadata_lasteyrie.json".format(COLLECTION_NAME)
TEMPLATE = "templates/manifest.json"
CANVAS = "templates/canvas.json"
ANNOTATION = "templates/annotationpage.json"
IMAGE = "templates/image.json"
COLLECTION = "templates/{0}/lasteyrie.json".format(COLLECTION_NAME)

# URLS
#Modifier ici pour mettre à jour avec les redirections
MANIFEST_URL_PREFIX = "https://iiif.chartes.psl.eu/lasteyrie"
COLLECTION_URL_PREFIX = "https://iiif.chartes.psl.eu/lasteyrie/collection"
IMAGE_URL_PREFIX = "https://iiif.chartes.psl.eu/images/lasteyrie"
#Pas de DTS
#DTS_COLLECTION_URL_PREFIX = "https://dev.chartes.psl.eu/dts/collections?id="
#DTS_DOCUMENT_URL_PREFIX = "https://dev.chartes.psl.eu/dts/document?id="
#PAS de website de consultation pour l'instant
#DOCUMENT_WEBSITE_URL_PREFIX = "https://dev.chartes.psl.eu/theses/document/"

# OUTPUT
MAN_DIST_DIR = "dist/manifests/{0}".format(COLLECTION_NAME)
COLL_DIST_DIR = "dist/collections/{0}".format(COLLECTION_NAME)

# SPECIFIC
SRC_IMAGES_PATH = "/home/cfaye/Bureau/IIIF_Image/"

if __name__ == "__main__":
    tmp = load_json(TEMPLATE)
    cv = load_json(CANVAS)
    metadata = load_json(METADATA)
    an = load_json(ANNOTATION)
    img = load_json(IMAGE)
    coll_tmp = load_json(COLLECTION)

    md = {"manifests": []}
    md_tmp = {}
    yearly_collections = {}

    for root, dirs, files in os.walk(SRC_IMAGES_PATH):
        for filename in files:
            if ".jpg" in filename:
                manifest_id = root.split("/")[-1]
                if manifest_id not in md_tmp:
                    md_tmp[manifest_id] = {
                        "id": manifest_id,
                        "label": manifest_id
                    }
                if "images" not in md_tmp[manifest_id]:
                    md_tmp[manifest_id]["images"] = []
                image_partial_id = "{0}/{1}/{2}".format(manifest_id, filename, "full/full/0/default.jpg")
                md_tmp[manifest_id]["images"].append(image_partial_id)
                md_tmp[manifest_id]["images"].sort()


#Ajout des métadonnées du document
    for m in md_tmp.values():
        metadata_manifest = copy.deepcopy(metadata)
        label_manifest = "Carnet de dessins de Robert de Lasteyrie"
        md["manifests"].append({
            "id": m["id"].lower(),
            "label": label_manifest,
            "images": m["images"],
            "metadata": metadata_manifest,
        })

    manifests = []
    # BUILD MANIFESTS
    for man in md["manifests"]:
        # Ajout des valeurs dans les metadonnées du manifest
        template = copy.deepcopy(tmp)
        template["id"] = "{0}/{1}/manifest".format(MANIFEST_URL_PREFIX, man["id"])
        # A reprendre en envoyant le label en meta
        template["label"] = {"fr": [man["label"]]}
        #template["homepage"][0]["id"] = "{0}{1}".format(DOCUMENT_WEBSITE_URL_PREFIX, man["id"].upper())
        #template["seeAlso"][0]["id"] = "{0}{1}".format(DTS_COLLECTION_URL_PREFIX, man["id"].upper())
        #Maj la valeur du sudoc ou la supprime selon la situation
        del template["seeAlso"]
        del template["homepage"]
        del template ["rendering"]
        #template["rendering"][0]["id"] = "{0}{1}".format(DTS_DOCUMENT_URL_PREFIX, man["id"].upper())
        template["partOf"][0]["id"] = "{0}/lasteyrie".format(COLLECTION_URL_PREFIX)
        template["metadata"] = man["metadata"]["metadata"]
        m = render_template(template, cv, an, img,
                            {"manifest": man, "collection": man["label"]},
                            MANIFEST_URL_PREFIX, IMAGE_URL_PREFIX)
        manifests.append(m)

        isExist = os.path.exists(MAN_DIST_DIR)
        if not isExist:
            os.makedirs(MAN_DIST_DIR)

        with open("{0}/{1}.json".format(MAN_DIST_DIR, man["id"].lower()), 'w') as f:
            f.write(json.dumps(m, indent=4, ensure_ascii=False))
        #Ajouter le contrôle avec l'API validator

    isExist = os.path.exists(COLL_DIST_DIR)
    if not isExist:
        os.makedirs(COLL_DIST_DIR)

    # BUILD COLLECTIONS
    #Remplacer collection_name par top
    #Remplacer collection_name par top
    with open("{0}/{1}.json".format(COLL_DIST_DIR, COLLECTION_NAME.lower()), 'w') as f:
        coll_name = "{0}/top".format(COLLECTION_URL_PREFIX)
        coll_label = {"fr": ["Carnet de dessins de Robert de Lasteyrie."]}
        coll_summary = {"fr": ["Carnet de dessins de Robert de Lasteyrie."]}
        toplevel_collection_items = []
        coll_thumb = sorted(manifests, key=lambda e: e["id"])[0]["thumbnail"][0]["id"]
        coll_seeAlso = ""
        manifests = sorted(manifests, key=lambda e: e["id"])
        toplevel_collection_items = sorted(toplevel_collection_items, key=lambda e: e["id"])
        toplevel_collection = render_collection(
            coll_tmp,
            manifests,
            coll_name,
            coll_label,
            coll_summary,
            coll_thumb,
            coll_seeAlso,
            item_type="Collection"
        )
        print(toplevel_collection)
        f.write(json.dumps(toplevel_collection, indent=4, ensure_ascii=False))

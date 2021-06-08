import json
import os
import pprint
import re
import csv
import copy

from tools.make_manifest import load_json, render_template, render_collection

#INFOS
COLLECTION_NAME = "encprom"

# TEMPLATES
METADATA = "meta/{0}/metadata_encprom.json".format(COLLECTION_NAME)
TEMPLATE = "templates/manifest.json"
CANVAS = "templates/canvas.json"
ANNOTATION = "templates/annotationpage.json"
IMAGE = "templates/image.json"
COLLECTION = "templates/{0}/collection_Photo_promo.json".format(COLLECTION_NAME)

# URLS
#Modifier ici pour mettre à jour avec les redirections
MANIFEST_URL_PREFIX = "https://iiif.chartes.psl.eu/encprom"
COLLECTION_URL_PREFIX = "https://iiif.chartes.psl.eu/encprom/collection"
IMAGE_URL_PREFIX = "https://iiif.chartes.psl.eu/images/encprom"
#Pas de DTS
#DTS_COLLECTION_URL_PREFIX = "https://dev.chartes.psl.eu/dts/collections?id="
#DTS_DOCUMENT_URL_PREFIX = "https://dev.chartes.psl.eu/dts/document?id="
#PAS de website de consultation pour l'instant
#DOCUMENT_WEBSITE_URL_PREFIX = "https://dev.chartes.psl.eu/theses/document/"

# OUTPUT
MAN_DIST_DIR = "dist/manifests/{0}".format(COLLECTION_NAME)
COLL_DIST_DIR = "dist/collections/{0}".format(COLLECTION_NAME)

# SPECIFIC
SRC_IMAGES_PATH = "/home/cfaye/Bureau/encprom/"

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
                name = filename.split("_")
                collection_id = name[1]
                manifest_id = "encprom_{0}_{1}_{2}".format(name[1], name[2], name[3])
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
                md_tmp[manifest_id]["year"] = name[1]
    print(md_tmp)
    #Ajout des métadonnées du document
    for m in md_tmp.values():
        metadata_manifest = copy.deepcopy(metadata)
        print(m['label'])
        if m['label'].split("_")[2] == "1":
            label_manifest = "Photographie numéro {1} des {2}er année de l'année {0} l'École nationale des chartes".format(m["year"], m['label'].split("_")[-1], m['label'].split("_")[2])
        else:
            label_manifest = "Photographie numéro {1} des {2}ème année de l'année {0} l'École nationale des chartes".format(
                m["year"], m['label'].split("_")[-1], m['label'].split("_")[2])
        metadata_manifest["metadata"][0]["value"]["fr"][0] = label_manifest
        metadata_manifest["metadata"][1]["value"]["fr"][0] = m["year"]
        md["manifests"].append({
            "id": m["id"].lower(),
            "label": label_manifest,
            "images": m["images"],
            "year": m["year"],
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
        template["partOf"][0]["id"] = "{0}/encprom_{1}".format(COLLECTION_URL_PREFIX, man["year"])
        template["metadata"] = man["metadata"]["metadata"]
        m = render_template(template, cv, an, img,
                            {"manifest": man, "collection": man["year"]},
                            MANIFEST_URL_PREFIX, IMAGE_URL_PREFIX, ["recto", "verso"])
        manifests.append(m)
        with open("{0}/{1}.json".format(MAN_DIST_DIR, man["id"].lower()), 'w') as f:
            f.write(json.dumps(m, indent=4, ensure_ascii=False))
        #Ajouter le contrôle avec l'API validator

        if not man["year"] in yearly_collections:
            yearly_collections[man["year"]] = []
        yearly_collections[man["year"]].append(m)

    # BUILD YEAR BASED COLLECTIONS
    for year, manifests in yearly_collections.items():
        coll_name = "{0}_{1}".format(COLLECTION_NAME.lower(), year)
        with open("{0}/{1}.json".format(COLL_DIST_DIR, coll_name.lower()), 'w') as f:
            coll_name = "{0}/{1}_{2}".format(COLLECTION_URL_PREFIX, COLLECTION_NAME.lower(), year)
            coll_label = {"fr": ["Photographie des promotions de l'École nationale des chartes en {0}".format(year)]}
            coll_summary = {"fr": ["Les photographies des différentes promotions de École nationale des chartes en {0}.".format(year)]}
            manifests = sorted(manifests, key=lambda e: e["id"])
            thumb = sorted(manifests, key=lambda e: e["id"])[0]["thumbnail"][0]["id"]
            yearly_collection = render_collection(coll_tmp, manifests , coll_name, coll_label, coll_summary, thumb)
            f.write(json.dumps(yearly_collection, indent=4, ensure_ascii=False))
        thumb = ""
    collection_data = []
    for year in yearly_collections.keys():
        name = "{0}_{1}".format(COLLECTION_NAME.lower(), year)
        thumb = []
        with open("{0}/{1}.json".format(COLL_DIST_DIR, name.lower()), 'r') as f:
            data = json.load(f)
            thumb = data["thumbnail"]
            f.close()
        collection_data.append({"year": year, "thumb":thumb})

    # BUILD COLLECTIONS
    #Remplacer collection_name par top
    with open("{0}/{1}.json".format(COLL_DIST_DIR, COLLECTION_NAME.lower()), 'w') as f:
        coll_name = "{0}/top".format(COLLECTION_URL_PREFIX)
        coll_label = {"fr": ["Photographie des promotions de l'École nationale des chartes"]}
        coll_summary = {"fr": ["Les photographies des différentes promotions de École nationale des chartes depuis 1904-1905"]}
        toplevel_collection_items = []
        coll_thumb = ""
        for data in collection_data:
            toplevel_collection_items.append(
                {
                    "id": "{0}/{1}_{2}".format(COLLECTION_URL_PREFIX, COLLECTION_NAME.lower(), data['year']),
                    "label": {"fr": ["Photographie des promotions de l'École nationale des chartes {0}".format(data['year'])]},
                    "thumbnail": data['thumb']
                })
        toplevel_collection_items = sorted(toplevel_collection_items, key=lambda e: e["id"])
        toplevel_collection = render_collection(
            coll_tmp,
            toplevel_collection_items,
            coll_name,
            coll_label,
            coll_summary,
            coll_thumb,
            item_type="Collection"
        )
        print(toplevel_collection)
        f.write(json.dumps(toplevel_collection, indent=4, ensure_ascii=False))


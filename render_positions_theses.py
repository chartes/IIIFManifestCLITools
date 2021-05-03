import json
import os
import pprint
import re

from tools.make_manifest import load_json, render_template, render_collection

# INFOS
PROJECT = "Positions_Theses_ENC"
COLLECTION_NAME = "encpos"
#Templates des metadatas pour encpos
METADATA = "meta/{0}/metadata_Positions_Theses_ENC.json".format(PROJECT)

# TEMPLATES
TEMPLATE = "templates/manifest.json"
CANVAS = "templates/canvas.json"
ANNOTATION = "templates/annotationpage.json"
IMAGE = "templates/image.json".format(PROJECT)
COLLECTION = "templates/{0}/collection_Positions_Theses_ENC.json".format(PROJECT)

# URLS
#Modifier ici pour mettre à jour avec les redirections
MANIFEST_URL_PREFIX = "https://iiif.chartes.psl.eu/manifests/encpos_test"
COLLECTION_URL_PREFIX = "https://iiif.chartes.psl.eu/collections/encpos_test"
IMAGE_URL_PREFIX = "https://iiif.chartes.psl.eu/images/encpos"
#Mettre à jour avec la version final des endpoint DTS
DTS_COLLECTION_URL_PREFIX = "https://dev.chartes.psl.eu/dts/collections?id="
DTS_DOCUMENT_URL_PREFIX = "https://dev.chartes.psl.eu/dts/document?id="
#URL de sortie
DOCUMENT_WEBSITE_URL_PREFIX = "https://theses.chartes.psl.eu/document/"

# OUTPUT
MAN_DIST_DIR = "dist/manifests/{0}".format("encpos_test")
COLL_DIST_DIR = "dist/collections/{0}".format("encpos_test")

# SPECIFIC
SRC_IMAGES_PATH = "/media/cfaye/Backup Plus/IIIF_Test/ENCPOS"
PATTERN = re.compile("([0-9]{4})/((ENCPOS_[0-9]{4})_[0-9]{2})/TIFF/(ENCPOS_[0-9]{4}_[0-9]{2}_[0-9]{2}.TIF)$")
# Ajout des metadata extern
EXTERNAL_METADATA = ""
#CANVAS_NAME_PATTERN = re.compile("ENCPOS_[0-9]{4}_([0-9]{2})")

if __name__ == "__main__":
    tmp = load_json(TEMPLATE)
    md = load_json(METADATA)
    cv = load_json(CANVAS)
    an = load_json(ANNOTATION)
    img = load_json(IMAGE)

    coll_tmp = load_json(COLLECTION)
    yearly_collections = {}

    # BUILD METADATA
    md_tmp = {}
    for root, dirs, files in os.walk(SRC_IMAGES_PATH):
        for filename in files:
            m = PATTERN.search(os.path.join(root, filename))
            if m:
                filename = m.group(4)
                year = m.group(1)
                manifest_id = m.group(2)
                collection_id = m.group(3)

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
                md_tmp[manifest_id]["year"] = year

    for m in md_tmp.values():
        md["manifests"].append({
            "id": m["id"],
            "label": m["label"],
            "images": m["images"],
            "year": m["year"]
        })

    manifests = []
    # BUILD MANIFESTS
    for man in md["manifests"]:
        #Ajout dans les metadonnées de la collection dans laquelle est membre le manifest
        m = render_template(tmp, cv, an, img,
                            {"metadata": md["metadata"],"manifest": man, "collection": man["year"]},
                            MANIFEST_URL_PREFIX, IMAGE_URL_PREFIX, COLLECTION_URL_PREFIX, DTS_COLLECTION_URL_PREFIX, DTS_DOCUMENT_URL_PREFIX, DOCUMENT_WEBSITE_URL_PREFIX)
        manifests.append(m)
        with open("{0}/{1}.json".format(MAN_DIST_DIR, man["id"]), 'w') as f:
            f.write(json.dumps(m, ensure_ascii=False))

        if not man["year"] in yearly_collections:
            yearly_collections[man["year"]] = []

        yearly_collections[man["year"]].append(m)

    # BUILD YEAR BASED COLLECTIONS
    for year, manifests in yearly_collections.items():
        coll_name = "{0}_{1}".format(COLLECTION_NAME, year)
        with open("{0}/{1}.json".format(COLL_DIST_DIR, coll_name), 'w') as f:
            coll_name = "{0}/{1}_{2}.json".format(COLLECTION_URL_PREFIX, COLLECTION_NAME, year)
            yearly_collection = render_collection(coll_tmp, manifests, coll_name)
            f.write(json.dumps(yearly_collection, ensure_ascii=False))

    # BUILD COLLECTIONS
    #Remplacer collection_name par top
    with open("{0}/{1}.json".format(COLL_DIST_DIR, COLLECTION_NAME), 'w') as f:
        coll_name = "{0}/{1}.json".format(COLLECTION_URL_PREFIX, COLLECTION_NAME)
        toplevel_collection_items = [
            {
                "id": "{0}/{1}_{2}.json".format(COLLECTION_URL_PREFIX, COLLECTION_NAME, year),
                "label": {"fr": "Positions de thèses de l'année {0}".format(year)}
            }
            for year in yearly_collections.keys()
        ]
        toplevel_collection = render_collection(
            coll_tmp,
            toplevel_collection_items,
            coll_name,
            item_type="Collection"
        )
        f.write(json.dumps(toplevel_collection, ensure_ascii=False))


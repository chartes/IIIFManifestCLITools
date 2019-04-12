import json
import pprint

from tools.make_manifest import load_json, render_template, render_collection

# INFOS
PROJECT = "Adele_CCI_2018_2019"
COLLECTION_NAME = "collection_CCI_2018_2019"
METADATA = "meta/{0}/metadata_CCI_2018_2019.json".format(PROJECT)

# TEMPLATES
TEMPLATE = "templates/manifest.json"
CANVAS = "templates/canvas.json"
COLLECTION = "templates/{0}/collection_CCI_2018_2019.json".format(PROJECT)
IMAGE = "templates/image.json".format(PROJECT)

# URLS
MANIFEST_URL_PREFIX = "https://iiif.chartes.psl.eu/manifests/adele/CCI"
COLLECTION_URL_PREFIX = "https://iiif.chartes.psl.eu/collections/adele"
IMAGE_URL_PREFIX = "https://iiif.chartes.psl.eu/images/adele/CCI"

# OUTPUT
MAN_DIST_DIR = "dist/manifests/{0}".format('CCI')
COLL_DIST_DIR = "dist/collections/{0}".format('CCI')


if __name__ == "__main__":
    tmp = load_json(TEMPLATE)
    md = load_json(METADATA)
    cv = load_json(CANVAS)
    img = load_json(IMAGE)
    coll_tmp = load_json(COLLECTION)

    manifests = []

    for man in md["manifests"]:
        m = render_template(tmp, cv, img,
                            {"metadata": md["metadata"], "manifest": man},
                            MANIFEST_URL_PREFIX, IMAGE_URL_PREFIX)
        manifests.append(m)
        with open("{0}/manifest{1}.json".format(MAN_DIST_DIR, man["id"]), 'w') as f:
            f.write(json.dumps(m, ensure_ascii=False))

    with open("{0}/{1}.json".format(COLL_DIST_DIR, COLLECTION_NAME), 'w') as f:
        coll_name = "{0}/{1}.json".format(COLLECTION_URL_PREFIX, COLLECTION_NAME)
        coll = render_collection(coll_tmp, manifests, coll_name)
        f.write(json.dumps(coll, ensure_ascii=False))


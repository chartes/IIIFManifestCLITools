import json
import copy
import click
import os
import csv
from tools.make_manifest import load_json, render_template, render_collection

#Pas de DTS
#DTS_COLLECTION_URL_PREFIX = "https://dev.chartes.psl.eu/dts/collections?id="
#DTS_DOCUMENT_URL_PREFIX = "https://dev.chartes.psl.eu/dts/document?id="
#PAS de website de consultation pour l'instant
#DOCUMENT_WEBSITE_URL_PREFIX = "https://dev.chartes.psl.eu/theses/document/"


# SPECIFIC

@click.command()
@click.argument('input', type=str)
@click.argument('output', type=str)
@click.argument('collection_name', type=str)
@click.argument('template_manifest', type=str)
@click.option('--template_collection', type=str, help='Enter the pat for the collections entry')
@click.option('--metadata_conf', type=str, help='Enter the path of metadata tsv files, the first line contains the label and the first column must be name "id" and have the names of the folder who contains the images.')
def main(input, output, collection_name, template_manifest, template_collection, metadata_conf):
    """
    INPUT: Enter the name of the folder who contains the images

    OUTPUT: Enter the destination path

    COLLECTION_NAME : Name of the image collection in IIIF SERVER

    TEMPLATE_METADATA : Path to the metadata json templates
    """
    #INPUT
    SRC_IMAGES_PATH = input

    # OUTPUT
    MAN_DIST_DIR = "{0}/manifests".format(output)
    COLL_DIST_DIR = "{0}/collections".format(output)

    # INFOS
    COLLECTION_NAME = collection_name

    # TEMPLATES
    METADATA = template_manifest
    TEMPLATE = "templates/manifest.json"
    CANVAS = "templates/canvas.json"
    ANNOTATION = "templates/annotationpage.json"
    IMAGE = "templates/image.json"
    LABELVALUE = "templates/labelvalue.json"
    if template_collection is None:
        COLLECTION = "templates/collection.json"
    else:
        COLLECTION = template_collection
    # URLS
    # Modifier ici pour mettre à jour avec les redirections
    MANIFEST_URL_PREFIX = "https://iiif.chartes.psl.eu/{0}".format(COLLECTION_NAME)
    COLLECTION_URL_PREFIX = "https://iiif.chartes.psl.eu/{0}/collection".format(COLLECTION_NAME)
    IMAGE_URL_PREFIX = "https://iiif.chartes.psl.eu/images/{0}".format(COLLECTION_NAME)

    tmp = load_json(TEMPLATE)
    cv = load_json(CANVAS)
    metadata = load_json(METADATA)
    an = load_json(ANNOTATION)
    img = load_json(IMAGE)
    coll_tmp = load_json(COLLECTION)
    metadata_canvaslabelvalue = load_json(LABELVALUE)

    md = {"manifests": []}
    md_tmp = {}
    list_metadata = []
    dict_metadata = {}
    if metadata_conf is not None:
        with open(metadata_conf, 'r', newline='') as meta:
            reader = csv.DictReader(meta, delimiter='\t', dialect="unix")
            for line in reader:
                dict_metadata[line["id"]] = line
                list_metadata.append(line)
    else:
        dict_metadata = None

    for root, dirs, files in os.walk(SRC_IMAGES_PATH):
        for filename in files:
            if ".jpg" or ".tif" in filename:
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

    # Ajout des métadonnées du document
    for m in md_tmp.values():
        metadata_manifest = copy.deepcopy(metadata)
        print(type(metadata_manifest["metadata"]))
        if dict_metadata is not None:
            try:
                for key, values in dict_metadata[m["id"]].items():
                    label_value = copy.deepcopy(metadata_canvaslabelvalue)
                    label_value["label"]["fr"] = key
                    label_value["value"]["fr"] = values
                    metadata_manifest["metadata"].append(label_value)
            except:
                print("{0} not present in metadata.tsv".format(m["id"]))
        #Ecrire le code en fonction des métadonnées correspondant
        label_manifest = m["label"]
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
        # template["homepage"][0]["id"] = "{0}{1}".format(DOCUMENT_WEBSITE_URL_PREFIX, man["id"].upper())
        # template["seeAlso"][0]["id"] = "{0}{1}".format(DTS_COLLECTION_URL_PREFIX, man["id"].upper())
        # Maj en fonction de la présence d'une sortie DTS, d'un site de consultation ou autre
        del template["seeAlso"]
        del template["homepage"]
        del template["rendering"]
        # template["rendering"][0]["id"] = "{0}{1}".format(DTS_DOCUMENT_URL_PREFIX, man["id"].upper())
        template["partOf"][0]["id"] = "{0}/{1}".format(COLLECTION_URL_PREFIX, COLLECTION_NAME)
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
        # Ajouter le contrôle avec l'API validator

    isExist = os.path.exists(COLL_DIST_DIR)
    if not isExist:
        os.makedirs(COLL_DIST_DIR)

    # BUILD COLLECTIONS
    # Remplacer collection_name par top
    # Remplacer collection_name par top
    with open("{0}/{1}.json".format(COLL_DIST_DIR, COLLECTION_NAME.lower()), 'w') as f:
        coll_name = "{0}/top".format(COLLECTION_URL_PREFIX)
        #Nom et sommaire des collections globales
        coll_label = {"fr": ["Nom Collection"]}
        coll_summary = {"fr": ["Nom Sommaire"]}
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
        f.write(json.dumps(toplevel_collection, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()

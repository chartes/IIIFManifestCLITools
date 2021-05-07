import json
import os
import pprint
import re
import csv
import copy

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
MANIFEST_URL_PREFIX = "https://iiif.chartes.psl.eu/encpos"
COLLECTION_URL_PREFIX = "https://iiif.chartes.psl.eu/encpos"
IMAGE_URL_PREFIX = "https://iiif.chartes.psl.eu/images/encpos"
#Mettre à jour avec la version final des endpoint DTS
DTS_COLLECTION_URL_PREFIX = "https://dev.chartes.psl.eu/dts/collections?id="
DTS_DOCUMENT_URL_PREFIX = "https://dev.chartes.psl.eu/dts/document?id="
#URL de sortie
DOCUMENT_WEBSITE_URL_PREFIX = "https://dev.chartes.psl.eu/theses/document/"

# OUTPUT
MAN_DIST_DIR = "dist/manifests/{0}".format("encpos")
COLL_DIST_DIR = "dist/collections/{0}".format("encpos")

# SPECIFIC
SRC_IMAGES_PATH = "/home/cfaye/Bureau/IIIF_Test/ENCPOS"
PATTERN = re.compile("([0-9]{4})/((ENCPOS_[0-9]{4})_[0-9]{2})/TIFF/(ENCPOS_[0-9]{4}_[0-9]{2}_[0-9]{2}.TIF)$")
EXTERNAL_METADATA = "meta/{0}/encpos.tsv".format(PROJECT)


#CANVAS_NAME_PATTERN = re.compile("ENCPOS_[0-9]{4}_([0-9]{2})")

if __name__ == "__main__":
    tmp = load_json(TEMPLATE)
    metadata = load_json(METADATA)
    cv = load_json(CANVAS)
    an = load_json(ANNOTATION)
    img = load_json(IMAGE)
    p = re.compile(r'<.*?>')

    coll_tmp = load_json(COLLECTION)
    yearly_collections = {}
    list_metadata = []
    md = {"manifests": []}
    with open(EXTERNAL_METADATA, 'r', newline='') as meta:
        reader = csv.DictReader(meta, delimiter='\t', dialect="unix")
        for line in reader:
            list_metadata.append(line)

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

    #Ajout des métadonnées du document
    for m in md_tmp.values():
        metadata_manifest = copy.deepcopy(metadata)
        for meta in list_metadata:
            #controle de travailler dans le même id
            if m["id"] == meta["id"]:
                list_delete = []
                #ajout de l'information du dc:creator
                metadata_manifest["metadata"][0]["value"]["fr"][0] = meta["title_rich"]
                # CLEANER LES CHAMPS AUTEURS
                if meta["author_idref-id"]!="" and meta["ark_databnf"] != "" and meta["link_wikipedia"] != "":
                    #ajout de l'information de l'auteur
                    metadata_manifest["metadata"][1]["value"]["fr"][0] = "{0}, <a href=\"https://www.idref.fr/{1}\">idref</a>, <a href=\"{2}\">wikipedia</a>, <a href=\"{3}\">BnF</a>".format(meta["NomComplet"], meta["author_idref-id"], meta["link_wikipedia"], meta["ark_databnf"])
                elif meta["author_idref-id"]!="" and meta["ark_databnf"] != "":
                    metadata_manifest["metadata"][1]["value"]["fr"][0] = "{0}, <a href=\"https://www.idref.fr/{1}\">idref</a>, <a href=\"{2}\">BnF</a>".format(meta["NomComplet"], meta["author_idref-id"], meta["ark_databnf"])
                elif meta["author_idref-id"] != "" :
                    metadata_manifest["metadata"][1]["value"]["fr"][0] = "{0}, <a href=\"https://www.idref.fr/{1}\">idref</a>".format(meta["NomComplet"], meta["author_idref-id"])
                else:
                    metadata_manifest["metadata"][1]["value"]["fr"][0] = meta["NomComplet"]
                #Ajout des informations pour le dc:publisher
                metadata_manifest["metadata"][2]["value"]["fr"][0] = "École nationale des chartes"
                # Ajout des informations pour le dc:source
                metadata_manifest["metadata"][3]["value"]["fr"][0] = "Positions des thèses soutenues par les élèves de la promotion de {0} pour obtenir le diplôme d'archiviste paléographe".format(m["year"])
                # Ajout des informations pour le dc:date
                metadata_manifest["metadata"][4]["value"]["fr"][0] = m["year"]
                for d in list_delete:
                    metadata_manifest["metadata"].pop(d)
                md["manifests"].append({
                    "id": m["id"].lower(),
                    "label": "{0}, {1}".format(meta["NomComplet"], p.sub('', meta["title_rich"])),
                    "images": m["images"],
                    "year": m["year"],
                    "first_page": int(meta["pagination"].split("-")[0]),
                    "metadata": metadata_manifest,
                    "sudoc": meta["these_ppn-sudoc"]
                })
                break


    manifests = []
    # BUILD MANIFESTS
    for man in md["manifests"]:
        # Ajout des valeurs dans les metadonnées du manifest
        template = copy.deepcopy(tmp)
        template["id"] = "{0}/{1}/manifest".format(MANIFEST_URL_PREFIX, man["id"])
        # A reprendre en envoyant le label en meta
        template["label"] = {"fr": [man["label"]]}
        template["homepage"][0]["id"] = "{0}{1}".format(DOCUMENT_WEBSITE_URL_PREFIX, man["id"].upper())
        template["seeAlso"][0]["id"] = "{0}{1}".format(DTS_COLLECTION_URL_PREFIX, man["id"].upper())
        #Maj la valeur du sudoc ou la supprime selon la situation
        if man["sudoc"] != "" :
            template["seeAlso"][1]["id"] = "https://www.sudoc.fr/{1}.xml".format(DTS_COLLECTION_URL_PREFIX, man["sudoc"])
        else:
            template["seeAlso"].pop(1)
        template["rendering"][0]["id"] = "{0}{1}".format(DTS_DOCUMENT_URL_PREFIX, man["id"].upper())
        template["partOf"][0]["id"] = "{0}{1}".format(COLLECTION_URL_PREFIX, man["year"])
        template["metadata"] = man["metadata"]["metadata"]
        m = render_template(template, cv, an, img,
                            {"manifest": man, "collection": man["year"]},
                            MANIFEST_URL_PREFIX, IMAGE_URL_PREFIX, man["first_page"])
        manifests.append(m)
        with open("{0}/{1}.json".format(MAN_DIST_DIR, man["id"].lower()), 'w') as f:
            f.write(json.dumps(m, ensure_ascii=False))
        #Ajouter le contrôle avec l'API validator

        if not man["year"] in yearly_collections:
            yearly_collections[man["year"]] = []
        print(man["year"])
        print(m)
        print("----------------------------------------------------------------------------------------")
        yearly_collections[man["year"]].append(m)

    # BUILD YEAR BASED COLLECTIONS
    for year, manifests in yearly_collections.items():
        coll_name = "{0}_{1}".format(COLLECTION_NAME.lower(), year)
        with open("{0}/{1}.json".format(COLL_DIST_DIR, coll_name.lower()), 'w') as f:
            coll_name = "{0}/{1}_{2}.json".format(COLLECTION_URL_PREFIX, COLLECTION_NAME.lower(), year)
            coll_label = {"fr": ["Positions des thèses de l’École des chartes soutenues en {0}".format(year)]}
            yearly_collection = render_collection(coll_tmp, manifests, coll_name, coll_label)
            f.write(json.dumps(yearly_collection, ensure_ascii=False))

    # BUILD COLLECTIONS
    #Remplacer collection_name par top
    with open("{0}/top.json".format(COLL_DIST_DIR), 'w') as f:
        coll_name = "{0}/{1}.json".format(COLLECTION_URL_PREFIX, COLLECTION_NAME.lower())
        coll_label = {"fr": "Positions des thèses de l’École des chartes"}
        toplevel_collection_items = [
            {
                "id": "{0}/{1}_{2}.json".format(COLLECTION_URL_PREFIX, COLLECTION_NAME.lower(), year),
                "label": {"fr": ["Positions des thèses de l'année {0}".format(year)]}
            }
            for year in yearly_collections.keys()
        ]
        toplevel_collection = render_collection(
            coll_tmp,
            toplevel_collection_items,
            coll_name,
            coll_label,
            item_type="Collection"
        )
        f.write(json.dumps(toplevel_collection, ensure_ascii=False))


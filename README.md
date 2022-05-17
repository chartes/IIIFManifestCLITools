# IIIFManifestCLITools

## Create virtual env

```
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirement.txt

```

## Usage 
```
render_folder_image.py --help 

Usage: render_folder_image.py [OPTIONS] INPUT COLLECTION_NAME OUTPUT TEMPLATE

    INPUT: Enter the name of the folder who contains the XML files or the differents folders who contains the XML files

    OUTPUT: Enter the destination path

    COLLECTION_NAME : Name of the image collection in IIIF SERVER


Options:
  --template TEXT  Path to the template of the collection.json files
  --help           Show this message and exit.

```
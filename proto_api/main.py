import os
from typing import Optional

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from core import create_property, add_property_to_image, add_image, get_images, create_tag, delete_image_property, \
    update_tag, get_tags, get_properties
from models import Property, Images, Tag, Image, Tags, Properties
from payloads import ImagePayload, PropertyPayload, AddImagePropertyPayload, AddTagPayload, DeleteImagePropertyPayload, \
    UpdateTagPayload

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO:
# ajouter une route static pour le mode serveur


# Route pour créer une property et l'insérer dans la table des properties
@app.post("/property")
def create_property_route(payload: PropertyPayload) -> Property:
    return create_property(payload.name, payload.type)


@app.get("/property")
def get_properties_route() -> Properties:
    return get_properties()

# Route pour ajouter une image
@app.post("/images")
def add_image_route(image: ImagePayload) -> Image:
    image = add_image(image.file_path)
    return image


# Route pour récupérer la liste de toutes les images
@app.get("/images")
def get_images_route() -> Images:
    images = get_images()
    return images


@app.get('/images/{file_path:path}')
def get_image(file_path: str):

    with open(file_path, 'rb') as f:
        data = f.read()

    ext = file_path.split('.')[-1]

    # # media_type here sets the media type of the actual response sent to the client.
    return Response(content=data, media_type="image/" + ext)


# Route pour ajouter une property à une image dans la table de jointure entre image et property
# On retourne le payload pour pouvoir valider l'update côté front
@app.post("/image_property")
def add_image_property(payload: AddImagePropertyPayload) -> AddImagePropertyPayload:
    add_property_to_image(payload.property_id, payload.sha1, payload.value)
    return payload


# Route pour supprimer une property d'une image dans la table de jointure entre image et property
@app.delete("/image_property")
def delete_property_route(payload: DeleteImagePropertyPayload) -> DeleteImagePropertyPayload:
    delete_image_property(payload.property_id, payload.sha1)
    return payload


@app.post("/tags")
def add_tag(payload: AddTagPayload) -> Tag:
    if not payload.parent_id:
        payload.parent_id = 0
    return create_tag(payload.property_id, payload.value, payload.parent_id)


@app.get("/tags")
def get_tags_route(property: Optional[str] = None) -> Tags:
    return get_tags(property)


@app.patch("/tags")
def update_tag_route(payload: UpdateTagPayload) -> Tag:
    return update_tag(payload)


@app.patch("/image_property")
def update_image_property(new_value: str = Body(..., embed=True)) -> str:
    pass


@app.patch("/property")
def update_property(payload: str):
    pass

# TODO: add update image property
# TODO: add update property
# TODO: add add folder
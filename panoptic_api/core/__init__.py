import atexit
import atexit
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from typing import List

from PIL import Image as pImage
from fastapi import HTTPException

import panoptic_api.core.db
from panoptic_api.core.queue import TransformManager
from panoptic_api.models import PropertyType, JSON, Image, Tag, Images, PropertyValue, Property, Tags, Properties, \
    UpdateTagPayload, UpdatePropertyPayload
from .image_importer import ImageImporter
from .. import panoptic

executor = ProcessPoolExecutor(max_workers=4)
atexit.register(executor.shutdown)
importer = ImageImporter(executor)


async def create_property(name: str, property_type: PropertyType) -> Property:
    return await db.add_property(name, property_type.value)


async def update_property(payload: UpdatePropertyPayload) -> Property:
    existing_property = await db.get_property_by_id(payload.id)
    if not existing_property:
        raise HTTPException(status_code=400, detail="Trying to modify non existent property")
    new_property = existing_property.copy(update=payload.dict(exclude_unset=True))
    await db.update_property(new_property)
    return new_property


async def get_properties() -> Properties:
    properties = await db.get_properties()
    return {prop.id: prop for prop in properties}


async def delete_property(property_id: str):
    await db.delete_property(property_id)


async def get_images() -> Images:
    """
    Get all images from database
    """
    rows = await db.get_images()
    result = {}
    for row in rows:
        sha1, paths, height, width, url, extension, name, property_id, value = row
        if sha1 not in result:
            result[sha1] = Image(sha1=sha1, paths=json.loads(paths), width=width, height=height, url=url, name=name,
                                 extension=extension)
        if property_id:
            result[sha1].properties[property_id] = PropertyValue(
                **{'property_id': property_id, 'value': db.decode_if_json(value)})
    return result


async def add_property_to_image(property_id: int, sha1: str, value: JSON) -> str:
    # first check that the property and the image exist:
    if await db.get_property_by_id(property_id) and await db.get_image_by_sha1(sha1):
        # check if a value already exists
        if await db.get_image_property(sha1, property_id):
            await db.update_image_property(sha1, property_id, value)
        else:
            await db.add_image_property(sha1, property_id, value)
        return value
    else:
        raise HTTPException(status_code=400, detail="Trying to set a value on a non existent property or sha1")


async def delete_image_property(property_id: int, sha1: str):
    await db.delete_image_property(property_id, sha1)


def _preprocess_image(file_path):
    image = pImage.open(file_path)
    name = file_path.split(os.sep)[-1]
    extension = name.split('.')[-1]
    width, height = image.size
    sha1_hash = hashlib.sha1(image.tobytes()).hexdigest()
    # TODO: gérer l'url statique quand on sera en mode serveur
    # url = os.path.join('/static/' + file_path.split(os.getenv('PANOPTIC_ROOT'))[1].replace('\\', '/'))
    url = f"/images/{file_path}"

    ahash, vector = _compute_ml(image)

    return file_path, name, extension, width, height, sha1_hash, url


def _compute_ml(image):
    # TODO: maybe move this function in core ? later if it works
    # TODO: use multiprocessing here ?
    ahash = panoptic.to_average_hash(image)
    # TODO: find a way to access all the images for PCA
    vector = panoptic.to_vector(image)
    # TODO: maybe add another queue to avoid bottleneck on db
    return ahash, vector


async def add_image(file_path) -> Image:
    _, name, extension, width, height, sha1_hash, url = _preprocess_image(file_path)
    # Vérification si sha1_hash existe déjà dans la table images
    return await add_image_to_db(file_path, name, extension, width, height, sha1_hash, url)


async def add_image_to_db(file_path, name, extension, width, height, sha1_hash, url) -> Image:
    image = await db.get_image_by_sha1(sha1_hash)
    # Si sha1_hash existe déjà, on ajoute file_path à la liste de paths
    if image:
        if file_path not in image.paths:
            image.paths.append(file_path)
            # Mise à jour de la liste de paths
            await db.update_image_paths(sha1_hash, json.dumps(image.paths))

    # Si sha1_hash n'existe pas, on l'ajoute avec la liste de paths contenant file_path
    else:
        await db.add_image(sha1_hash, height, width, name, extension, json.dumps([file_path]), url)
    return await db.get_image_by_sha1(sha1_hash)


async def add_folder(folder):
    folders = (await db.get_parameters()).folders
    await db.update_folders(list({folder, *folders}))

    found = importer.import_folder(save_callback, folder)
    print(f'found {found} images')
    return found


async def save_callback(image, file_path, name, extension, width, height, sha1_hash, url):
    await add_image_to_db(file_path, name, extension, width, height, sha1_hash, url)

    importer.compute_image(get_compute_callback(sha1_hash), image=image)


def get_compute_callback(sha1):
    async def callback(ahash, vector):
        await db.update_image_hashs(sha1, str(ahash), vector)
    return callback


async def create_tag(property_id, value, parent_id) -> Tag:
    existing_tag = await db.get_tag(property_id, value)
    if existing_tag is not None:
        if await db.tag_in_ancestors(existing_tag.id, parent_id):
            raise HTTPException(status_code=400, detail="Adding a tag that is an ancestor of himself")
        existing_tag.parents = list({*existing_tag.parents, parent_id})
        await db.update_tag(existing_tag)
        tag_id = existing_tag.id
    else:
        parents = [parent_id]
        tag_id = await db.add_tag(property_id, value, json.dumps(parents))
    return await db.get_tag_by_id(tag_id)


async def update_tag(payload: UpdateTagPayload) -> Tag:
    existing_tag = await db.get_tag_by_id(payload.id)
    if not existing_tag:
        raise HTTPException(status_code=400, detail="Trying to modify non existent tag")
    if await db.tag_in_ancestors(existing_tag.id, payload.parent_id):
        raise HTTPException(status_code=400, detail="Adding a tag that is an ancestor of himself")
    # change only fields of the tags that are set in the payload
    new_tag = existing_tag.copy(update=payload.dict(exclude_unset=True))
    await db.update_tag(new_tag)
    return new_tag


async def delete_tag(tag_id: int) -> List[int]:
    # first delete the tag
    modified_tags = [await db.delete_tag_by_id(tag_id)]
    # when deleting a tag, get all children of this tag
    children = await db.get_tags_by_parent_id(tag_id)
    # and remove parent ref of tag in children
    [modified_tags.extend(await delete_tag_parent(c, tag_id)) for c in children]
    # then get all images properties tagged with it
    image_properties = await db.get_image_properties_with_tag(tag_id)
    # and delete the tag ref from them
    for image_property in image_properties:
        image_property.value.remove(tag_id)
        await db.update_image_property(image_property.sha1, image_property.property_id, image_property.value)
    return modified_tags


async def delete_tag_parent(tag_id: int, parent_id: int) -> List[int]:
    tag = await db.get_tag_by_id(tag_id)
    tag.parents.remove(parent_id)
    if not tag.parents:
        return await delete_tag(tag.id)
    else:
        await db.update_tag(tag)
        return []


async def get_tags(prop: str = None) -> Tags:
    res = {}
    tag_list = await db.get_tags(prop)
    for tag in tag_list:
        if tag.property_id not in res:
            res[tag.property_id] = {}
        res[tag.property_id][tag.id] = tag
    return res

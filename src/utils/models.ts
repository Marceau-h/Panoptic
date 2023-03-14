import { ComputedRef } from "vue";

export enum PropertyType {
    string = "string",
    number = "number",
    tag = "tag",
    multi_tags = "multi_tags",
    image_link = "image_link",
    url = "url",
    date = "date",
    path = "path",
    color = "color",
    checkbox = "checkbox"
}

export interface Tag {
    id: number;
    property_id: number;
    parents: number[];
    value: string;
    color?: string;
}

export interface Property {
    id: number
    name: string
    type: PropertyType
}

export interface PropertyValue extends Property {
    value: any
}

export interface Image {
    sha1: string
    width: number
    height: number
    url: string
    paths: [string]
    extension: string
    properties?: {
        [id:number]: PropertyValue
    }
}

export interface Images {
    [sha1:string]: Image
}

export interface Properties {
    [id:number]: Property
}

export interface Tags {
    [property_id: number]: {
        [id: number]: Tag
    }
}

// a tag inside a tagstree
export interface TreeTag{
    name: string
    id: number
    children: TagsTree
    localId: string
}

export interface TagsTree {
    [tagId: number]: TreeTag
}

export interface PropsTree {
    [propId:number]: TagsTree
}

export interface GlobalStore {
    tags: Tags,
    tagTrees: ComputedRef<PropsTree>
    properties: Properties
    images: Images
    imageList: ComputedRef<{url: String, imageName: String}[]>
    [otherOptions: string]: unknown
}
<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { globalStore } from '@/data/store';
import { Image, Modals, Property, PropertyRef, PropertyType, Sha1Pile } from '@/data/models';
import PropertyInput from '@/components/inputs/PropertyInput.vue';
import ColorPropInput from '@/components/inputs/ColorPropInput.vue';
import PropertyIcon from '@/components/properties/PropertyIcon.vue';
import TagInput from '@/components/inputs/TagInput.vue';
import SelectCircle from '@/components/inputs/SelectCircle.vue';

const props = defineProps({
    image: Object as () => Image,
    pile: Object as () => Sha1Pile,
    similarity: Number,
    size: { type: Number, default: 100 },
    index: Number,
    groupId: String,
    hideProperties: Boolean,
    constraintWidth: Boolean,
    noBorder: Boolean,
    properties: Array<Property>,
    selected: Boolean,
    selectedPreview: Boolean
})

const emits = defineEmits(['resize', 'update:selected'])

const image = computed(() => props.image ?? props.pile.images[0])

const containerElem = ref(null)
const hover = ref(false)

function hasProperty(propertyId: number) {
    return image.value.properties[propertyId] && image.value.properties[propertyId].value !== undefined
}

const imageProperties = computed(() => {
    let res: Array<PropertyRef> = []
    props.properties.forEach((p: Property) => {
        let propRef: PropertyRef = {
            propertyId: p.id,
            type: p.type,
            value: hasProperty(p.id) ? image.value.properties[p.id].value : undefined,
            imageId: image.value.id,
            mode: p.mode
        }
        res.push(propRef)

    });
    return res
})

const imageSizes = computed(() => {
    let ratio = image.value.width / image.value.height

    let h = props.size
    let w = h * ratio

    if (ratio > 2) {
        w = props.size * 2
        h = w / ratio
    }

    return { width: w, height: h }
})

const imageContainerStyle = computed(() => `width: ${Math.max(imageSizes.value.width, props.size) - 2}px; height: ${props.size}px;`)
const imageStyle = computed(() => `width: ${imageSizes.value.width - 2}px; height: ${imageSizes.value.height}px;`)
const width = computed(() => Math.max(Number(props.size), imageSizes.value.width))
const widthStyle = computed(() => `width: ${Math.max(Number(props.size), imageSizes.value.width)}px;`)
</script>

<template>
    <div class="full-container" :style="widthStyle" :class="(!props.noBorder ? 'img-border' : '')" ref="containerElem">
        <!-- {{ props.image.containerRatio }} -->
        <div :style="imageContainerStyle" class="img-container" @click="globalStore.showModal(Modals.IMAGE, image)"
            @mouseenter="hover = true" @mouseleave="hover = false">
            <div v-if="props.pile?.similarity" class="simi-ratio" >{{ Math.floor(props.pile.similarity * 100) }}</div>
            <img :src="props.size < 150 ? image.url : image.fullUrl" :style="imageStyle" />

            <div v-if="hover || props.selected" class="w-100 box-shadow" :style="imageContainerStyle"></div>
            <SelectCircle v-if="hover || props.selected" :model-value="props.selected"
                @update:model-value="v => emits('update:selected', v)" class="select" :light-mode="true" />
        </div>
        <div class="image-count" v-if="props.pile?.images.length > 1">{{ props.pile.images.length }}</div>
        <div class="prop-container" v-if="imageProperties.length > 0 && !props.hideProperties">
            <div v-for="property, index in imageProperties">
                <div class="custom-hr ms-2 me-2" v-if="index > 0"></div>
                <TagInput v-if="property.type == PropertyType.multi_tags || property.type == PropertyType.tag"
                    :property="property" :max-size="String(props.size)" :mono-tag="property.type == PropertyType.tag"
                    :input-id="[...props.groupId.split('-').map(Number), property.propertyId, props.index]" />
                <div v-else-if="property.type == PropertyType.color" class="d-flex flex-row">
                    <PropertyIcon :type="property.type" style="line-height: 25px; margin-right:2px;" />
                    <ColorPropInput class="mt-1 ms-0" :rounded="true" :image="image"
                        :property="globalStore.properties[property.propertyId]" :width="width - 22" :min-height="20" />
                </div>
                <PropertyInput v-else :property="property" :max-size="String(props.size)"
                    :input-id="[...props.groupId.split('-').map(Number), property.propertyId, props.index]" />
            </div>
        </div>
        <div v-if="props.selectedPreview" class="w-100 h-100"
            style="position: absolute; top:0; left: 0; background-color: rgba(0, 0, 255, 0.127);"></div>
    </div>
</template>

<style scoped>

.image-count {
    position: absolute;
    top: 0;
    right: 0;
    padding: 0px 4px;
    background-color: var(--border-color);
    color: var(--grey-text);
    font-size: 10px;
    line-height: 15px;
    margin: 2px;
    border-radius: 5px;
    z-index: 100;
}

.simi-ratio {
    position: absolute;
    bottom: 0;
    right: 0;
    padding: 0px 4px;
    background-color: var(--border-color);
    color: var(--grey-text);
    font-size: 10px;
    line-height: 15px;
    margin: 2px;
    border-radius: 5px;
    z-index: 100;
}

.full-container {
    position: relative;
}

.img-border {
    border: 1px solid var(--border-color);
}

.img-container {
    position: relative;
    margin: auto;
    padding: auto;
    cursor: pointer;
}

.prop-container {
    width: 100%;
    border-top: 1px solid var(--border-color);
    padding: 2px;
    font-size: 12px;
}

img {
    max-height: 100%;
    max-width: 100%;
    /* width: auto;
    height: auto; */
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    margin: auto;
}

.select {
    position: absolute;
    top: 0;
    left: 5px;
}

.box-shadow {
    position: relative;
}

.box-shadow::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    -webkit-box-shadow: inset 0px 24px 25px -20px rgba(0, 0, 0, 0.3);
    -moz-box-shadow: inset 0px 24px 25px -20px rgba(0, 0, 0, 0.3);
    box-shadow: inset 0px 50px 30px -30px rgba(0, 0, 0, 0.5);
    overflow: hidden;
}
</style>
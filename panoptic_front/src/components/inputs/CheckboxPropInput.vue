<script setup lang="ts">
import { Image, Property } from '@/data/models';
import { getImageProperty } from '@/utils/utils';
import { computed, onMounted, ref, watch } from 'vue';
import TextInput from './TextInput.vue';
import { globalStore } from '@/data/store';

const props = defineProps({
    property: Object as () => Property,
    image: Object as () => Image,
    width: Number,
    minHeight: { type: Number, default: 30 }

})
const emits = defineEmits({ 'update:height': Number })

const elem = ref(null)
// const inputElem = computed(() => elem.value.inputElem)

const propRef = computed(() => getImageProperty(props.image.id, props.property.id))
// const isFocus = computed(() => elem.value?.isFocus)

function focus() {
    elem.value.focus()
}

function toggle() {
    globalStore.setPropertyValue(props.property.id, props.image, !propRef.value.value)
}

// function updateFromStore() {
//     localValue.value = propRef.value.value ?? ''
// }

// function save() {
//     globalStore.setPropertyValue(props.property.id, props.image, localValue.value)
// }


// onMounted(updateFromStore)
// watch(propRef, updateFromStore)


defineExpose({
    // localValue,
    // inputElem
    focus
})

// watch(localValue, save)


</script>

<template>
    <div class="container d-flex flex-row" :style="{height: props.minHeight+'px'}">
        <input type="checkbox" v-model="propRef.value" @click.stop.prevent="toggle"/>
    </div>
</template>

<style scoped>
.container {
    padding-top: 0px;
}

input {
    margin-left: 4px;
}

</style>

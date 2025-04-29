<template>
  <v-select
    :model-value="modelValue"
    :items="models"
    item-title="name"
    item-value="name"
    label="Model"
    density="compact"
    hide-details
    class="model-selector"
    @update:model-value="handleModelChange"
  >
    <template v-slot:item="{ item }">
      <v-icon
        v-if="item.raw.supportsVision"
        icon="mdi-eye"
        class="mr-2"
      ></v-icon>
      {{ item.raw.name }}
    </template>
  </v-select>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

interface Model {
  name: string
  supportsVision: boolean
}

export default defineComponent({
  name: 'ModelSelector',
  props: {
    models: {
      type: Array as () => Model[],
      required: true
    },
    modelValue: {
      type: String,
      required: true
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const handleModelChange = (model: string) => {
      emit('update:modelValue', model)
    }

    return {
      handleModelChange
    }
  }
})
</script>

<style scoped>
.model-selector {
  max-width: 200px;
}
</style> 
<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="500">
    <v-card>
      <v-card-title>Settings</v-card-title>
      <v-card-text>
        <v-select
          v-model="localModel"
          :items="availableModels"
          item-title="name"
          item-value="name"
          label="Select Model"
          @update:model-value="handleModelChange"
          variant="outlined"
        ></v-select>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue'

interface Model {
  name: string
  supportsVision: boolean
}

export default defineComponent({
  name: 'SettingsDialog',
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    availableModels: {
      type: Array as () => Model[],
      required: true
    },
    selectedModel: {
      type: String,
      required: true
    }
  },
  emits: ['update:modelValue', 'model-change'],
  setup(props, { emit }) {
    const localModel = ref(props.selectedModel)

    watch(() => props.selectedModel, (newValue) => {
      localModel.value = newValue
    })

    const handleModelChange = () => {
      const selectedModelObj = props.availableModels.find(model => model.name === localModel.value)
      emit('model-change', selectedModelObj)
    }

    return {
      localModel,
      handleModelChange
    }
  }
})
</script> 
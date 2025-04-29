<template>
  <v-dialog v-model="show" max-width="800px">
    <v-card>
      <v-card-title class="d-flex align-center">
        <span>Debug Panel</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="show = false"></v-btn>
      </v-card-title>
      
      <v-card-text>
        <v-textarea
          v-model="debugLog"
          readonly
          auto-grow
          rows="20"
          variant="outlined"
          class="font-family-monospace"
        ></v-textarea>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue'

export default defineComponent({
  name: 'DebugPanel',
  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    messages: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const show = ref(props.modelValue)
    const debugLog = ref('')

    watch(() => props.modelValue, (newValue) => {
      show.value = newValue
    })

    watch(show, (newValue) => {
      emit('update:modelValue', newValue)
    })

    watch(() => props.messages, (newMessages) => {
      debugLog.value = JSON.stringify(newMessages, null, 2)
    }, { deep: true })

    return {
      show,
      debugLog
    }
  }
})
</script>

<style scoped>
.font-family-monospace {
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
}
</style> 
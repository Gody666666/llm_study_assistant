<template>
  <v-app>
    <v-main>
      <v-container fluid>
        <v-row>
          <v-col cols="12" md="3">
            <v-card>
              <v-card-title>Model Selection</v-card-title>
              <v-card-text>
                <v-select
                  v-model="selectedModel"
                  :items="availableModels"
                  item-title="name"
                  item-value="name"
                  label="Select Model"
                  @update:model-value="handleModelChange"
                ></v-select>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="9">
            <v-card>
              <v-card-title>Chat Interface</v-card-title>
              <v-card-text>
                <v-textarea
                  v-model="prompt"
                  label="Enter your prompt"
                  rows="3"
                  auto-grow
                  @keydown.enter.prevent="sendPrompt"
                ></v-textarea>
                <v-file-input
                  v-if="supportsVision"
                  v-model="imageFile"
                  label="Upload Image"
                  accept="image/*"
                  prepend-icon="mdi-camera"
                ></v-file-input>
                <v-btn
                  color="primary"
                  @click="sendPrompt"
                  :loading="isLoading"
                  :disabled="!prompt.trim()"
                >
                  Send
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-card>
              <v-card-title>Response</v-card-title>
              <v-card-text>
                <div class="response-text" v-html="formattedResponse"></div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import axios from 'axios'

interface Model {
  name: string
  supportsVision: boolean
}

export default defineComponent({
  name: 'App',
  setup() {
    const selectedModel = ref('')
    const availableModels = ref<Model[]>([])
    const prompt = ref('')
    const response = ref('')
    const imageFile = ref<File | null>(null)
    const isLoading = ref(false)
    const supportsVision = computed(() => {
      const model = availableModels.value.find(m => m.name === selectedModel.value)
      return model?.supportsVision || false
    })

    const formattedResponse = computed(() => {
      return response.value.replace(/\n/g, '<br>')
    })

    const fetchModels = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/models')
        availableModels.value = response.data
        if (availableModels.value.length > 0) {
          selectedModel.value = availableModels.value[0].name
        }
      } catch (error) {
        console.error('Error fetching models:', error)
      }
    }

    const handleModelChange = () => {
      response.value = ''
      imageFile.value = null
    }

    const sendPrompt = async () => {
      if (!prompt.value.trim()) return

      isLoading.value = true
      response.value = ''

      try {
        const formData = new FormData()
        formData.append('prompt', prompt.value)
        if (imageFile.value && supportsVision.value) {
          formData.append('image', imageFile.value)
        }

        const axiosResponse = await axios.post(
          `http://localhost:5000/api/chat/${selectedModel.value}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            responseType: 'text',
          }
        )

        // Split the response into lines and process each SSE message
        const lines = axiosResponse.data.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.response) {
                response.value += data.response
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      } catch (error) {
        console.error('Error sending prompt:', error)
        response.value = 'Error: Failed to get response from the model'
      } finally {
        isLoading.value = false
      }
    }

    // Fetch models when component is mounted
    fetchModels()

    return {
      selectedModel,
      availableModels,
      prompt,
      response,
      imageFile,
      isLoading,
      supportsVision,
      formattedResponse,
      handleModelChange,
      sendPrompt,
    }
  },
})
</script>

<style scoped>
.response-text {
  white-space: pre-wrap;
  font-family: monospace;
}
</style> 
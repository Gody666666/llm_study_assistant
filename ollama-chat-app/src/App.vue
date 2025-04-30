<template>
  <v-app>
    <AppBar 
      @open-settings="showSettings = true"
      @open-debug="showDebugPanel = true; fetchRawMessages()"
    />
    
    <SettingsDialog
      v-model="showSettings"
      :available-models="availableModels"
      :selected-model="selectedModel"
      @model-change="handleModelChange"
    />

    <DebugPanel
      v-model="showDebugPanel"
      :messages="rawMessages"
    />

    <!-- Main Content -->
    <v-main class="main-content">
      <v-container fluid class="fill-height pa-0">
        <v-row no-gutters class="fill-height">
          <!-- Chat Panel (Left Side - 70%) -->
          <v-col cols="8" class="d-flex fill-height">
            <ChatPanel
              v-model:chatHistory="chatHistory"
              :selected-model="selectedModel"
              :is-loading="isLoading"
              :modelInfo="currentModelInfo"
              @new-chat="startNewChat"
            />
          </v-col>

          <!-- Textbook Panel (Right Side - 30%) -->
          <v-col cols="4" class="grey-lighten-4 fill-height">
            <TextbookPanel />
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue'
import axios from 'axios'
import AppBar from './components/AppBar.vue'
import SettingsDialog from './components/SettingsDialog.vue'
import ChatPanel from './components/ChatPanel.vue'
import TextbookPanel from './components/TextbookPanel.vue'
import DebugPanel from './components/DebugPanel.vue'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  image?: string
}

interface Model {
  name: string
  supportsVision: boolean
}

export default defineComponent({
  name: 'App',
  components: {
    AppBar,
    SettingsDialog,
    ChatPanel,
    TextbookPanel,
    DebugPanel
  },
  setup() {
    const showSettings = ref(false)
    const selectedModel = ref('')
    const availableModels = ref<Model[]>([])
    const isLoading = ref(false)
    const showDebugPanel = ref(false)
    const rawMessages = ref([])
    const chatHistory = ref<ChatMessage[]>([
      {
        role: 'assistant',
        content: 'Hi there! I\'m your study buddy. How can I help you today?'
      }
    ])

    const currentModelInfo = computed(() => {
      return availableModels.value.find(model => model.name === selectedModel.value) || {
        name: '',
        supportsVision: false
      }
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

    const fetchRawMessages = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/chat/raw-messages')
        rawMessages.value = response.data.messages
      } catch (error) {
        console.error('Error fetching raw messages:', error)
      }
    }

    const handleModelChange = (model: Model) => {
      selectedModel.value = model.name
      chatHistory.value = [{
        role: 'assistant',
        content: 'Hi there! I\'m your study buddy. How can I help you today?'
      }]
    }

    const startNewChat = () => {
      chatHistory.value = [{
        role: 'assistant',
        content: 'Hi there! I\'m your study buddy. How can I help you today?'
      }]
    }

    onMounted(() => {
      fetchModels()
    })

    return {
      showSettings,
      selectedModel,
      availableModels,
      isLoading,
      showDebugPanel,
      rawMessages,
      chatHistory,
      handleModelChange,
      startNewChat,
      fetchRawMessages,
      currentModelInfo
    }
  }
})
</script>

<style scoped>
.main-content {
  height: 100vh;
  overflow: hidden;
}

.fill-height {
  height: 100%;
}
</style> 
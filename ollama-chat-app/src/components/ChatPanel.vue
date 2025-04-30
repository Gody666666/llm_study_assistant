<template>
  <v-card class="d-flex flex-column fill-height w-100">
    <!-- New Chat Button -->
    <v-card-text class="py-2 flex-grow-0">
      <v-btn
        prepend-icon="mdi-plus"
        variant="outlined"
        class="mb-2"
        block
        @click="$emit('new-chat')"
      >
        New chat
      </v-btn>
    </v-card-text>

    <!-- Chat Messages -->
    <v-card-text class="flex-grow-1 overflow-y-auto chat-container pa-4" ref="chatContainer">
      <div class="d-flex flex-column justify-start">
        <template v-for="(message, index) in chatHistory" :key="index">
          <v-card
            :class="['mb-3', message.role === 'user' ? 'ml-auto' : 'mr-auto', message.image ? 'chat-message-with-image' : '']"
            :color="message.role === 'user' ? 'primary' : 'white'"
            :dark="message.role === 'user'"
            max-width="80%"
            :variant="message.role === 'assistant' ? 'outlined' : 'flat'"
            class="chat-message"
          >
            <v-card-text :class="message.role === 'assistant' ? 'text-body-1 font-weight-medium text-grey-darken-3' : ''">
              <div v-html="message.content"></div>
              <div v-if="message.image" class="mt-2">
                <v-img
                  :src="message.image"
                  max-width="400"
                  max-height="400"
                  cover
                  class="rounded"
                ></v-img>
              </div>
            </v-card-text>
          </v-card>
        </template>

        <!-- Typing Indicator -->
        <v-card
          v-if="isWaitingForResponse"
          class="mb-3 mr-auto chat-message typing-indicator"
          max-width="80%"
          variant="outlined"
        >
          <v-card-text class="d-flex align-center">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="ml-2 text-grey-darken-2">Thinking...</span>
          </v-card-text>
        </v-card>
      </div>
    </v-card-text>

    <!-- Input Area -->
    <div class="chat-input-area">
      <v-card-text class="pt-2 pb-0">
        <v-textarea
          class="my-1"
          v-model="localPrompt"
          rows="3"
          auto-grow
          hide-details
          placeholder="Ask a question..."
          @keydown.enter.prevent="handleSend"
          variant="outlined"
          density="comfortable"
          :max-rows="6"
          :disabled="isWaitingForResponse"
        ></v-textarea>
      </v-card-text>
      <v-card-actions class="pa-4 pt-0">
        <v-tooltip
          :text="supportsVision ? 'Upload an image to use with the model' : 'Current model does not support image input'"
          location="top"
        >
          <template v-slot:activator="{ props: tooltipProps }">
            <div v-bind="tooltipProps">
              <v-file-input
                v-model="localImageFile"
                hide-details
                class="shrink"
                accept="image/*"
                icon="mdi-camera"
                variant="plain"
                density="comfortable"
                :disabled="isWaitingForResponse || !supportsVision"
              ></v-file-input>
            </div>
          </template>
        </v-tooltip>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          :loading="isLoading"
          :disabled="!localPrompt.trim() || isWaitingForResponse"
          @click="handleSend"
        >
          <template v-if="isWaitingForResponse">
            <v-progress-circular
              indeterminate
              color="white"
            ></v-progress-circular>
          </template>
          <template v-else>
            Send
          </template>
        </v-btn>
      </v-card-actions>
    </div>
  </v-card>
</template>

<script lang="ts">
import { defineComponent, ref, watch, onMounted, computed } from 'vue'
import axios from 'axios'
import { AIMessage, HumanMessage, BaseMessage } from '@langchain/core/messages'

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
  name: 'ChatPanel',
  props: {
    chatHistory: {
      type: Array as () => ChatMessage[],
      required: true
    },
    selectedModel: {
      type: String,
      required: true
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    modelInfo: {
      type: Object as () => Model,
      required: true
    }
  },
  emits: ['update:chatHistory', 'new-chat'],
  setup(props, { emit }) {
    const localPrompt = ref('')
    const localImageFile = ref<File | null>(null)
    const isWaitingForResponse = ref(false)
    const chatContainer = ref<HTMLElement | null>(null)

    const supportsVision = computed(() => props.modelInfo?.supportsVision || false)

    const scrollToBottom = () => {
      if (chatContainer.value) {
        setTimeout(() => {
          chatContainer.value!.scrollTop = chatContainer.value!.scrollHeight
        }, 100)
      }
    }

    watch(() => props.chatHistory, () => {
      scrollToBottom()
    }, { deep: true })

    const createImagePreview = (file: File): Promise<string> => {
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target?.result as string)
        reader.readAsDataURL(file)
      })
    }

    const parseLangChainMessage = (message: string): string => {
      try {
        // Try to parse as JSON first
        const parsed = JSON.parse(message)
        if (parsed.content) {
          return parsed.content
        }
      } catch (e) {
        // If not JSON, try to parse as LangChain message
        if (message.includes('AIMessage(content=')) {
          // Extract the content part
          const contentMatch = message.match(/content=(.*?)(?:\)|$)/)
          if (contentMatch) {
            let content = contentMatch[1]
            // Handle nested Response objects
            if (content.includes('Response(content=\'')) {
              const responseMatch = content.match(/Response\(content='(.*?)'\)/)
              if (responseMatch) {
                return responseMatch[1].replace(/\\'/g, "'")
              }
            }
            // Handle nested AIMessage with Response
            if (content.includes('AIMessage(content="Response(content=\'')) {
              const nestedMatch = content.match(/Response\(content='(.*?)'\)/)
              if (nestedMatch) {
                return nestedMatch[1].replace(/\\'/g, "'")
              }
            }
            // Clean up any remaining quotes and escaped characters
            return content.replace(/^['"]|['"]$/g, '').replace(/\\'/g, "'")
          }
        }
        // Handle direct Response format
        if (message.includes('Response(content=\'')) {
          const responseMatch = message.match(/Response\(content='(.*?)'\)/)
          if (responseMatch) {
            return responseMatch[1].replace(/\\'/g, "'")
          }
        }
      }
      return message
    }

    const handleSend = async () => {
      if (!localPrompt.value.trim() && !localImageFile.value) return
      if (isWaitingForResponse.value) return

      const userMessage: ChatMessage = {
        role: 'user',
        content: localPrompt.value
      }

      if (localImageFile.value) {
        userMessage.image = await createImagePreview(localImageFile.value)
      }

      const newChatHistory = [...props.chatHistory, userMessage]
      emit('update:chatHistory', newChatHistory)
      scrollToBottom()

      isWaitingForResponse.value = true
      localPrompt.value = ''

      try {
        const formData = new FormData()
        formData.append('prompt', userMessage.content)
        if (localImageFile.value) {
          formData.append('image', localImageFile.value)
        }

        // Ensure we have a valid model name
        const modelName = props.selectedModel || 'llama3.1:latest'
        const response = await axios.post(
          `http://localhost:5000/api/chat/${modelName}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            responseType: 'text',
            timeout: 30000
          }
        )

        let assistantMessage = ''
        const lines = response.data.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.response) {
                assistantMessage = parseLangChainMessage(data.response)
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }

        if (assistantMessage) {
          emit('update:chatHistory', [...newChatHistory, {
            role: 'assistant',
            content: assistantMessage
          }])
        } else {
          emit('update:chatHistory', [...newChatHistory, {
            role: 'assistant',
            content: 'I apologize, but I couldn\'t process your request.'
          }])
        }
        scrollToBottom()
      } catch (error: any) {
        console.error('Error sending prompt:', error)
        emit('update:chatHistory', [...newChatHistory, {
          role: 'assistant',
          content: error.code === 'ECONNABORTED' 
            ? 'The request timed out. Please try again.'
            : 'I apologize, but I encountered an error while processing your request.'
        }])
        scrollToBottom()
      } finally {
        isWaitingForResponse.value = false
        localImageFile.value = null
      }
    }

    const newChat = async () => {
      try {
        // Clear chat history on the backend
        await axios.delete('http://localhost:5000/api/chat/history')
        emit('new-chat')
      } catch (error) {
        console.error('Error clearing chat history:', error)
      }
    }

    return {
      localPrompt,
      localImageFile,
      isWaitingForResponse,
      chatContainer,
      handleSend,
      newChat,
      supportsVision
    }
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  background-color: rgb(248, 249, 250);
  overflow-y: auto;
  height: 100%;
}

.chat-container > div {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.chat-input-area {
  background-color: white;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.chat-message {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
  max-width: 75% !important;
}

.chat-message-with-image {
  min-width: 200px !important;
}

.chat-message.v-card--variant-outlined {
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
}

.typing-indicator {
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.typing-dots {
  display: flex;
  align-items: center;
  gap: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  background-color: #666;
  border-radius: 50%;
  animation: typing 1s infinite;
  display: inline-block;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}
</style> 
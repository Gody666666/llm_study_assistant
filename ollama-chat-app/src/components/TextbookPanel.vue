<template>
  <div class="textbook-panel">
    <h2>Textbooks</h2>
    <div v-if="loading" class="loading">
      Loading textbooks...
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else class="textbooks">
      <div v-for="(textbook, id) in textbooks" :key="id" class="textbook">
        <div class="textbook-header">
          <img 
            v-if="textbook.cover_image" 
            :src="getPreviewUrl(textbook.cover_image)" 
            :alt="textbook.title"
            class="textbook-cover"
          />
          <h3>{{ textbook.title }}</h3>
        </div>
        <div class="chapters">
          <div 
            v-for="chapter in textbook.chapters" 
            :key="chapter.hash"
            class="chapter"
          >
            <div class="chapter-preview">
              <img 
                v-if="chapter.preview_image" 
                :src="getPreviewUrl(chapter.preview_image)" 
                :alt="chapter.title"
              />
            </div>
            <div class="chapter-info">
              <h4>{{ chapter.title }}</h4>
              <p>Pages: {{ chapter.num_pages }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import axios from 'axios'

interface Chapter {
  hash: string
  title: string
  preview_image: string | null
  num_pages: number
}

interface Textbook {
  title: string
  cover_image: string | null
  chapters: Chapter[]
}

interface Textbooks {
  [key: string]: Textbook
}

export default defineComponent({
  name: 'TextbookPanel',
  setup() {
    const textbooks = ref<Textbooks>({})
    const loading = ref(true)
    const error = ref<string | null>(null)

    const fetchTextbooks = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/pdf/index')
        textbooks.value = response.data
      } catch (err) {
        error.value = 'Failed to load textbooks'
        console.error('Error loading textbooks:', err)
      } finally {
        loading.value = false
      }
    }

    const getPreviewUrl = (path: string): string => {
      return `http://localhost:5000/api/pdf/preview/${path}`
    }

    fetchTextbooks()

    return {
      textbooks,
      loading,
      error,
      getPreviewUrl
    }
  }
})
</script>

<style scoped>
.textbook-panel {
  padding: 1rem;
  background-color: #f5f5f5;
  border-radius: 8px;
  height: 100%;
  overflow-y: auto;
}

.textbook {
  margin-bottom: 2rem;
  background-color: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.textbook-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.textbook-cover {
  width: 80px;
  height: 120px;
  object-fit: cover;
  border-radius: 4px;
  margin-right: 1rem;
}

.textbook h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.chapters {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.chapter {
  background-color: #f8f9fa;
  border-radius: 6px;
  overflow: hidden;
  transition: transform 0.2s;
}

.chapter:hover {
  transform: translateY(-2px);
}

.chapter-preview {
  height: 120px;
  overflow: hidden;
}

.chapter-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chapter-info {
  padding: 0.5rem;
}

.chapter-info h4 {
  margin: 0;
  font-size: 1rem;
  color: #333;
}

.chapter-info p {
  margin: 0.5rem 0 0;
  font-size: 0.9rem;
  color: #666;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #dc3545;
  padding: 1rem;
  text-align: center;
  background-color: #f8d7da;
  border-radius: 4px;
  margin: 1rem 0;
}
</style>
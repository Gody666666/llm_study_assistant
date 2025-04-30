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
      <div v-for="book in textbooks" :key="book.book_title" class="textbook-section">
        <div class="textbook-header">
          <img :src="getPreviewUrl(book.cover_image)" :alt="book.title" class="textbook-cover">
          <h3>{{ book.title }}</h3>
        </div>
        <div class="chapters-list">
          <div v-for="chapter in sortedChapters(book.chapters)" 
               :key="chapter.chapter" 
               class="chapter-item"
               :class="{ 'selected': book.selectedChapters.includes(chapter.chapter) }"
               @click="toggleChapter(book, chapter)">
            <img :src="getPreviewUrl(chapter.preview_image)" :alt="chapter.title" class="chapter-preview">
            <span>{{ chapter.title }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import axios from 'axios'

interface Chapter {
  chapter: string
  preview_image: string
  order: number
  title: string
  hash: string
}

interface Textbook {
  book_title: string
  cover_image: string
  chapters: Chapter[]
  title: string
  selectedChapters: string[]
}

interface Textbooks {
  [key: string]: Textbook
}

export default defineComponent({
  name: 'TextbookPanel',
  setup(props, { emit }) {
    const textbooks = ref<Textbooks>({})
    const loading = ref(true)
    const error = ref<string | null>(null)

    const fetchTextbooks = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/pdf/index')
        const books = response.data
        Object.keys(books).forEach(bookKey => {
          books[bookKey].selectedChapters = []
        })
        textbooks.value = books
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

    const sortedChapters = (chapters: Chapter[]) => {
      return [...chapters].sort((a, b) => a.order - b.order)
    }

    const toggleChapter = async (book: Textbook, chapter: Chapter) => {
      const index = book.selectedChapters.indexOf(chapter.chapter)
      if (index === -1) {
        book.selectedChapters.push(chapter.chapter)
      } else {
        book.selectedChapters.splice(index, 1)
      }
      
      try {
        // Get all selected PDF hashes directly from the chapter metadata
        const selectedHashes = book.selectedChapters.map(chapterName => {
          const chapter = book.chapters.find(c => c.chapter === chapterName)
          return chapter?.hash || null
        }).filter(hash => hash !== null)
        
        emit('chapters-change', {
          bookTitle: book.book_title,
          selectedChapters: book.selectedChapters,
          pdfHashes: selectedHashes
        })
      } catch (error) {
        console.error('Error getting PDF hashes:', error)
      }
    }

    onMounted(() => {
      fetchTextbooks()
    })

    return {
      textbooks,
      loading,
      error,
      getPreviewUrl,
      sortedChapters,
      toggleChapter
    }
  },
  emits: ['chapters-change']
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

.textbook-section {
  margin-bottom: 2rem;
  background-color: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.textbook-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.textbook-cover {
  width: 60px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.textbook h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.chapters-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
}

.chapter-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.chapter-item:hover {
  background-color: #e0e0e0;
}

.chapter-item.selected {
  background-color: #e3f2fd;
  border: 2px solid #2196f3;
}

.chapter-preview {
  width: 100px;
  height: 140px;
  object-fit: cover;
  border-radius: 4px;
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
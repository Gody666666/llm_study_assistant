<template>
  <v-card flat class="fill-height">
    <v-card-text class="overflow-y-auto h-100">
      <!-- Textbook Section -->
      <div class="text-h6 mb-4">Science</div>
      <v-img
        src="https://placehold.co/400x300"
        class="mb-4 rounded-lg"
        alt="Science Textbook Cover"
      ></v-img>

      <!-- Chapters List -->
      <v-list>
        <v-list-item
          v-for="chapter in chapters"
          :key="chapter.id"
          :title="chapter.title"
          :prepend-avatar="chapter.icon"
          class="mb-2"
          rounded="lg"
          variant="outlined"
        ></v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

interface Chapter {
  id: number
  title: string
  icon: string
}

export default defineComponent({
  name: 'TextbookPanel',
  setup() {
    const chapters = ref<Chapter[]>([
      { id: 1, title: 'Chapter 1', icon: 'https://placehold.co/40x40' },
      { id: 2, title: 'Chapter 2', icon: 'https://placehold.co/40x40' },
      { id: 3, title: 'Chapter 3', icon: 'https://placehold.co/40x40' }
    ])

    return {
      chapters
    }
  }
})
</script>
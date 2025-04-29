<template>
  <v-app-bar color="indigo darken-1" dark>
    <v-app-bar-title>Study Buddy</v-app-bar-title>
    <v-spacer></v-spacer>
    <v-btn icon @click="$emit('open-settings')">
      <v-icon>mdi-cog</v-icon>
    </v-btn>
  </v-app-bar>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'AppBar',
  emits: ['open-settings']
})
</script> 
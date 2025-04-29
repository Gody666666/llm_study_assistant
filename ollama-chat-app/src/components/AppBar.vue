<template>
  <v-app-bar color="indigo darken-1" dark>
    <v-app-bar-title>Study Buddy</v-app-bar-title>
    <v-spacer></v-spacer>
    <v-btn
      icon="mdi-bug"
      variant="text"
      @click="$emit('open-debug')"
    ></v-btn>
    <v-btn
      icon="mdi-cog"
      variant="text"
      @click="$emit('open-settings')"
    ></v-btn>
  </v-app-bar>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'AppBar',
  emits: ['open-settings', 'open-debug']
})
</script> 
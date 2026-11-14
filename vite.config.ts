import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './',
  plugins: [react()],
  // The Godot export lives in Juego/ and is served as-is at /juego.html.
  publicDir: 'Juego',
})

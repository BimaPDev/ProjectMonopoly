"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

type ThemeProviderProps = {
  children: React.ReactNode
  storageKey?: string
}

export function ThemeProvider({ children, storageKey = "vite-ui-theme" }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      storageKey={storageKey}
    >
      {children}
    </NextThemesProvider>
  )
}

export { useTheme } from 'next-themes'


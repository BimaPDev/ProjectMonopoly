import { ThemeProvider as NextThemesProvider } from "next-themes";
import { useEffect, useState } from "react";

function App() {
  const [mounted, setMounted] = useState(false);

  // useEffect only runs on the client, so now we can safely show the UI
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
      <div className="min-h-screen bg-white dark:bg-zinc-950">
        {/* Your existing app content */}
      </div>
    </NextThemesProvider>
  );
}

export default App;

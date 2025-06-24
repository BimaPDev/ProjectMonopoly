export async function login(email: string, password: string) {
    try {
        const response = await fetch(`${import.meta.env.VITE_API_CALL}/api/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) throw new Error("Login failed");

        const data = await response.json();

        // 🔹 Store the token securely (either in localStorage or an HTTP-only cookie)
        localStorage.setItem("token", data.token);
        localStorage.setItem("sessionId", data.sessionId);

        return data;
    } catch (error) {
        console.error("Login Error:", error);
        throw error;
    }
}

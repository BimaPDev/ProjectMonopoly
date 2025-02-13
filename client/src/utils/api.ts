export async function fetchProtectedData() {
    const token = localStorage.getItem("token");
    if (!token) {
        throw new Error("No token found, please log in");
    }

    const response = await fetch("http://localhost:8080/api/protected/dashboard", {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (!response.ok) throw new Error("Unauthorized or expired token");

    return response.text();
}

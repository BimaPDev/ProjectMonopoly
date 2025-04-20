import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const token = localStorage.getItem("token");

        if (token) {
            setIsAuthenticated(true);
        } else {
            setIsAuthenticated(false);
            navigate("/login", { state: { from: location.pathname } }); // Redirect to login and remember the page user wanted
        }
    }, [navigate, location.pathname]);

    // 🔹 Prevent UI flashing before auth check is complete
    if (isAuthenticated === null) return <div>Loading...</div>;

    return isAuthenticated ? children : null;
}

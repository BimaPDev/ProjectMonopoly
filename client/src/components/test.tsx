import React, { useState } from "react";

const TestPage: React.FC = () => {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) {
      setResponse("Session ID is required.");
      return;
    }

    setLoading(true);
    setResponse(null);

    // System-managed user_id and group_id
    const user_id = 1; // You can fetch this from auth or global state
    const group_id = 1; // Same as above, from system data
    const session_id = input.trim(); // User-provided session ID

    const payload = {
      user_id,
      group_id,
      session_id,
    };

    try {
      const res = await fetch("http://67.217.246.210:8080/tiktok_session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
    } catch (error) {
      setResponse("Failed to send request.");
    } finally {
      setLoading(false);
    }
  };

  const isError = response?.includes("Failed") || response?.includes("required");

  return (
    <div className="min-h-screen flex items-center justify-center bg-black p-4">
      <div className="bg-white p-6 rounded-2xl shadow-xl w-full max-w-md">
        <h1 className="text-xl font-bold mb-4 text-center">Send a POST Request</h1>

        <input
          type="text"
          placeholder="Enter your session ID"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            setResponse(null);
          }}
          className="w-full border border-gray-300 p-2 rounded-xl mb-4"
        />

        <button
          onClick={handleSend}
          disabled={loading}
          className={`w-full p-2 rounded-xl text-white transition ${
            loading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Sending..." : "Send"}
        </button>

        {response && (
          <pre
            className={`mt-4 p-3 rounded-xl text-sm whitespace-pre-wrap break-all ${
              isError ? "bg-red-500 text-white" : "bg-gray-100"
            }`}
          >
            {response}
          </pre>
        )}
      </div>
    </div>
  );
};

export default TestPage;

export default function LandingPage() {
  return (
    <div 
      className="min-h-screen text-white"
      style={{
        background: "linear-gradient(135deg, #222, #000)",
        backgroundSize: "cover"
      }}
    >
      <div className="container mx-auto px-4 py-12 flex flex-col items-center">
        <div className="w-full max-w-md mb-12">
          <img 
            src="https://dogwoodgaming.com/wp-content/uploads/2021/12/dogwood-gaming-logo.png" 
            alt="Dogwood Gaming Logo"
            className="w-full object-contain"
          />
        </div>
        
        <div className="text-center mb-16">
          <h1 className="text-5xl font-extrabold tracking-wide mb-6 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            Marketing Tool
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Elevate your brand with Dogwood Gaming's professional marketing suite.
          </p>
        </div>
        
        {/* Card with buttons */}
        <div className="bg-gray-900 bg-opacity-70 p-8 rounded-xl shadow-2xl border border-gray-800 max-w-md w-full">
          <h2 className="text-2xl font-bold mb-6 text-center">Ready to Level Up?</h2>
          
          <div className="space-y-4">
            <a
              href="/login"
              className="block w-full py-3 px-6 bg-purple-600 text-white font-semibold rounded-md text-center transition duration-300 transform hover:bg-purple-700 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-opacity-50"
            >
              Sign In
            </a>
            
            <a
              href="/register"
              className="block w-full py-3 px-6 bg-gradient-to-r from-pink-500 to-purple-600 text-white font-semibold rounded-md text-center transition duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-opacity-50"
            >
              Create Account
            </a>
          </div>
        </div>
        
        
        <div className="mt-16 text-center text-gray-500 text-sm">
        <p>© 2025 Dogwood Gaming. All rights reserved.</p>
        <span>
          <a 
            href="https://dogwoodgaming.com/" 
            className="transition-all duration-200 hover:text-purple-400 hover:underline"
          >
            Home page
          </a> | <a 
            href="https://dogwoodgaming.com/contact-us/" 
            className="transition-all duration-200 hover:text-purple-400 hover:underline"
          >
            Contact us
          </a>
        </span> 
      </div>
      </div>
    </div>
  );
}
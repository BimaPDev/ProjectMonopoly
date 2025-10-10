import { LoginForm } from "@/components/login-form"
export default function LoginPage() {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-black min-h-svh md:p-10">
      <div className="w-full max-w-sm md:max-w-3xl">
        <LoginForm />
      </div>
    </div>
  )
}
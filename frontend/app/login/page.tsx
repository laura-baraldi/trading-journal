"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../../lib/supabase";
import { API_URL, SITE_URL } from "../../lib/api";
import Image from "next/image";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [confirmPassword, setConfirmPassword] = useState("");

  const router = useRouter();

  async function handleLogin() {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setMessage(error.message);
      return;
    }

    router.push("/");
  }

  async function handleDemoLogin() {
    setMessage("");

    try {
      const response = await fetch(`${API_URL}/demo-login`, {
        method: "POST",
      });

      if (!response.ok) {
        setMessage("Demo login unavailable.");
        return;
      }

      const data = await response.json();

      const { error } = await supabase.auth.setSession({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });

      if (error) {
        setMessage(error.message);
        return;
      }

      router.push("/");
    } catch {
      setMessage("Demo login unavailable.");
    }
  }

  async function handleSignUp() {
    if (password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }
    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      setMessage(error.message);
      return;
    }

    setMessage("Check your email to confirm your account.");
  }

  async function handleForgotPassword() {
    if (!email) {
      setMessage("Enter your email first.");
      return;
    }

    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${SITE_URL}/reset-password`,
    });

    if (error) {
      setMessage(error.message);
      return;
    }

    setMessage("Check your email for a password reset link.");
  }
  return (
    <main className="min-h-screen bg-[#f8fbff] text-slate-900">
      {/* Desktop */}
      <div className="relative hidden min-h-screen overflow-hidden px-6 py-10 sm:block">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-[42%] h-[720px] w-[1000px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-100/60 blur-3xl" />
        </div>

        <div className="pointer-events-none absolute inset-0 opacity-[0.12]">
          <svg
            viewBox="0 0 1400 800"
            className="h-full w-full"
            preserveAspectRatio="none"
          >
            <path
              d="M0 650
                        C120 610, 170 540, 240 500
                        S350 390, 420 430
                        S520 510, 610 440
                        S720 330, 810 350
                        S930 300, 1010 240
                        S1180 170, 1400 90"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-blue-400"
            />

            {[
              [70, 590, 22, 70],
              [130, 550, 22, 85],
              [190, 500, 22, 75],
              [250, 450, 22, 95],
              [320, 400, 22, 75],
              [390, 420, 22, 95],
              [470, 450, 22, 65],
              [550, 405, 22, 85],
              [630, 360, 22, 70],
              [710, 325, 22, 90],
              [790, 310, 22, 65],
              [870, 285, 22, 85],
              [950, 250, 22, 70],
              [1030, 215, 22, 90],
              [1110, 180, 22, 70],
              [1190, 145, 22, 90],
              [1270, 105, 22, 75],
              [1340, 70, 22, 95],
            ].map(([x, y, width, height]) => (
              <g key={x}>
                <line
                  x1={x + width / 2}
                  y1={y - 18}
                  x2={x + width / 2}
                  y2={y + height + 18}
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-blue-400"
                />

                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  rx="3"
                  fill="currentColor"
                  className="text-blue-400"
                />
              </g>
            ))}
          </svg>
        </div>

        <div className="relative z-10 mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl flex-col items-center justify-center">
          <div className="w-full max-w-[480px] rounded-[28px] border border-slate-200/70 bg-white/95 px-8 py-8 shadow-[0_25px_75px_rgba(15,23,42,0.14)] backdrop-blur-sm">
            <div className="text-center">
              <div className="mx-auto h-16 w-16 overflow-hidden rounded-2xl shadow-lg shadow-blue-200/70">
                <Image
                  src="/favicon.ico"
                  alt="Trading Journal"
                  width={64}
                  height={64}
                  className="h-full w-full object-cover"
                />
              </div>

              <h1 className="mt-4 text-4xl font-bold tracking-tight">
                Trading Journal
              </h1>

              <p className="mt-2 text-base text-slate-500">
                Track trades. Review performance. Improve decisions.
              </p>
            </div>

            <div className="my-6 h-px bg-slate-200" />

            <h2 className="text-center text-xl font-semibold">
              {mode === "signin" ? "Sign in" : "Create account"}
            </h2>

            {mode === "signup" && (
              <p className="mt-1 text-center text-sm text-slate-500">
                Start tracking your trades in one place.
              </p>
            )}

            <div className="mt-6 flex flex-col gap-5">
              <div>
                <label
                  htmlFor="email-desktop"
                  className="mb-1.5 block text-sm font-medium text-slate-700"
                >
                  Email
                </label>

                <div className="relative">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                  >
                    <rect x="3" y="5" width="18" height="14" rx="2" />
                    <path d="m4 7 8 6 8-6" />
                  </svg>

                  <input
                    id="email-desktop"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    className="w-full rounded-lg border border-slate-300 bg-white py-3.5 pl-10 pr-4 text-base outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password-desktop"
                  className="mb-1.5 block text-sm font-medium text-slate-700"
                >
                  Password
                </label>

                <div className="relative">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                  >
                    <rect x="5" y="10" width="14" height="10" rx="2" />
                    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                  </svg>

                  <input
                    id="password-desktop"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Enter your password"
                    className="w-full rounded-lg border border-slate-300 bg-white py-3.5 pl-10 pr-4 text-base outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                </div>

                {mode === "signin" && (
                  <button
                    type="button"
                    onClick={handleForgotPassword}
                    className="mt-2 cursor-pointer text-sm font-medium text-blue-600 hover:underline"
                  >
                    Forgot your password?
                  </button>
                )}
              </div>

              {mode === "signup" && (
                <div>
                  <label
                    htmlFor="confirm-password-desktop"
                    className="mb-1.5 block text-sm font-medium text-slate-700"
                  >
                    Confirm password
                  </label>

                  <input
                    id="confirm-password-desktop"
                    type="password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    placeholder="Confirm your password"
                    className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3.5 text-base outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                </div>
              )}

              <button
                type="button"
                onClick={mode === "signin" ? handleLogin : handleSignUp}
                className="group relative flex cursor-pointer items-center justify-center rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 px-5 py-3.5 text-base font-semibold text-white shadow-md shadow-blue-200 transition hover:from-blue-700 hover:to-blue-800"
              >
                <span>{mode === "signin" ? "Sign in" : "Create account"}</span>

                <span className="absolute right-4">→</span>
              </button>

              <button
                type="button"
                onClick={handleDemoLogin}
                className="cursor-pointer rounded-lg border border-blue-500 bg-white px-5 py-3 text-sm font-semibold text-blue-600 transition hover:bg-blue-50"
              >
                Try demo
              </button>

              {message && (
                <p className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  {message}
                </p>
              )}

              <p className="text-center text-sm text-slate-500">
                {mode === "signin"
                  ? "Don't have an account?"
                  : "Already have an account?"}

                <button
                  type="button"
                  onClick={() => {
                    setMode(mode === "signin" ? "signup" : "signin");
                    setPassword("");
                    setConfirmPassword("");
                    setMessage("");
                  }}
                  className="ml-1 cursor-pointer font-semibold text-blue-600 hover:underline"
                >
                  {mode === "signin" ? "Create one" : "Sign in"}
                </button>
              </p>
            </div>
          </div>

          <div className="mt-8 grid w-full max-w-[860px] overflow-hidden rounded-2xl border border-slate-200 bg-white/95 shadow-[0_12px_35px_rgba(15,23,42,0.08)] backdrop-blur-sm sm:grid-cols-3">
            <div className="flex items-center gap-4 px-6 py-6">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                ◔
              </div>

              <div>
                <h3 className="text-[15px] font-semibold">
                  Advanced analytics
                </h3>
                <p className="mt-1 text-[13px] leading-5 text-slate-500">
                  Visualize your performance with clear charts.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 border-x border-slate-200 px-6 py-6">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                ▣
              </div>

              <div>
                <h3 className="text-[15px] font-semibold">Trade tracking</h3>
                <p className="mt-1 text-[13px] leading-5 text-slate-500">
                  Record and review your trades in one place.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 px-6 py-6">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                ↗
              </div>

              <div>
                <h3 className="text-[15px] font-semibold">
                  Improve consistently
                </h3>
                <p className="mt-1 text-[13px] leading-5 text-slate-500">
                  Learn from data and make better decisions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile */}
      <div className="relative flex min-h-[100dvh] sm:hidden">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-blue-100/70 blur-3xl" />
          <div className="absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-slate-200/60 blur-3xl" />
        </div>

        <div className="relative z-10 mx-auto flex min-h-[100dvh] w-full max-w-[430px] flex-col px-4 py-4">
          <div className="flex flex-1 flex-col justify-center">
            <div className="mb-4 text-center">
              <div className="mx-auto h-11 w-11 overflow-hidden rounded-xl shadow-[0_8px_20px_rgba(37,99,235,0.18)]">
                <Image
                  src="/favicon.ico"
                  alt="Trading Journal"
                  width={64}
                  height={64}
                  className="h-full w-full object-cover"
                />
              </div>

              <h1 className="mt-2.5 text-[24px] font-bold leading-tight tracking-tight text-slate-900">
                Trading Journal
              </h1>

              <p className="mt-1 text-[13px] leading-5 text-slate-500">
                Track trades. Review performance. Improve.
              </p>
            </div>

            <div className="rounded-[22px] border border-slate-200/90 bg-white/95 px-4 py-4 shadow-[0_18px_45px_rgba(15,23,42,0.10)] backdrop-blur-sm">
              <div className="mb-4 text-center">
                <h2 className="text-[20px] font-semibold leading-tight text-slate-900">
                  {mode === "signin" ? "Sign in" : "Create account"}
                </h2>

                {mode === "signup" && (
                  <p className="mt-1 text-[12px] leading-4 text-slate-500">
                    Start tracking your trades in one place.
                  </p>
                )}
              </div>

              <div className="flex flex-col gap-3">
                <div>
                  <label
                    htmlFor="email-mobile"
                    className="mb-1 block text-[12px] font-medium text-slate-700"
                  >
                    Email
                  </label>

                  <div className="relative">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    >
                      <rect x="3" y="5" width="18" height="14" rx="2" />
                      <path d="m4 7 8 6 8-6" />
                    </svg>

                    <input
                      id="email-mobile"
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      placeholder="you@example.com"
                      className="h-11 w-full rounded-xl border border-slate-300 bg-white pl-9 pr-3 text-[14px] outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-3 focus:ring-blue-100"
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <label
                      htmlFor="password-mobile"
                      className="text-[12px] font-medium text-slate-700"
                    >
                      Password
                    </label>

                    {mode === "signin" && (
                      <button
                        type="button"
                        onClick={handleForgotPassword}
                        className="cursor-pointer text-[12px] font-medium text-blue-600 hover:underline"
                      >
                        Forgot password?
                      </button>
                    )}
                  </div>

                  <div className="relative">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    >
                      <rect x="5" y="10" width="14" height="10" rx="2" />
                      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                    </svg>

                    <input
                      id="password-mobile"
                      type="password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="Enter your password"
                      className="h-11 w-full rounded-xl border border-slate-300 bg-white pl-9 pr-3 text-[14px] outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-3 focus:ring-blue-100"
                    />
                  </div>
                </div>

                {mode === "signup" && (
                  <div>
                    <label
                      htmlFor="confirm-password-mobile"
                      className="mb-1 block text-[12px] font-medium text-slate-700"
                    >
                      Confirm password
                    </label>

                    <input
                      id="confirm-password-mobile"
                      type="password"
                      value={confirmPassword}
                      onChange={(event) =>
                        setConfirmPassword(event.target.value)
                      }
                      placeholder="Confirm your password"
                      className="h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-[14px] outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-3 focus:ring-blue-100"
                    />
                  </div>
                )}

                <button
                  type="button"
                  onClick={mode === "signin" ? handleLogin : handleSignUp}
                  className="relative mt-1 flex h-11 cursor-pointer items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-blue-700 px-4 text-[14px] font-semibold text-white shadow-[0_8px_20px_rgba(37,99,235,0.22)] transition active:scale-[0.99]"
                >
                  <span>
                    {mode === "signin" ? "Sign in" : "Create account"}
                  </span>

                  <span className="absolute right-4">→</span>
                </button>

                <button
                  type="button"
                  onClick={handleDemoLogin}
                  className="cursor-pointer rounded-lg border border-blue-500 bg-white px-5 py-3 text-sm font-semibold text-blue-600 transition hover:bg-blue-50"
                >
                  Try demo
                </button>

                {message && (
                  <p className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[12px] leading-4 text-slate-600">
                    {message}
                  </p>
                )}

                <p className="text-center text-[12px] leading-4 text-slate-500">
                  {mode === "signin"
                    ? "Don't have an account?"
                    : "Already have an account?"}

                  <button
                    type="button"
                    onClick={() => {
                      setMode(mode === "signin" ? "signup" : "signin");
                      setPassword("");
                      setConfirmPassword("");
                      setMessage("");
                    }}
                    className="ml-1 cursor-pointer font-semibold text-blue-600 hover:underline"
                  >
                    {mode === "signin" ? "Create one" : "Sign in"}
                  </button>
                </p>
              </div>
            </div>

            {mode === "signin" && (
              <div className="mt-3 flex items-center justify-center gap-2 text-[11px] font-medium text-slate-400">
                <span>Analytics</span>
                <span>•</span>
                <span>Trade tracking</span>
                <span>•</span>
                <span>Improve</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export function baseUrl(): string {
  return process.env.REACT_APP_BASE_URL as string
}

export function urlFor(...parts: string[]): string {
  const url = new URL(baseUrl())
  url.pathname = parts.join('/')
  return url.toString()
}

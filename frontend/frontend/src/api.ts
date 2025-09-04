export async function api<T>(path:string, init:RequestInit={}) {
  const res = await fetch(path, { headers:{ 'Accept':'application/json', ...init.headers }, ...init })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const getHealth = () => api<{status:string;version:string}>('/api/v1/health')
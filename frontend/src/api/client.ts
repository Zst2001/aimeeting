import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '',
  timeout: 5_000,
})

export type HealthResponse = {
  status: 'ok'
}

export async function getBackendHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}

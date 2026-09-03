export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  request_id: string
}

import api from "./api";

interface HealthResponse {
  status: string;
}

export async function getApplicationHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
}

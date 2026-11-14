import api from "./api";

interface HealthResponse {
  status: string;
  database: string;
}

export async function getApplicationHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health/ready");
  return response.data;
}

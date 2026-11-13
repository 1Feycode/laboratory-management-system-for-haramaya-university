export type AppRole =
  | "ULMD_ADMIN"
  | "MAINTENANCE_TECH"
  | "LAB_MANAGER"
  | "LAB_TECH"
  | "AUDITOR";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: AppRole;
  department_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthSession {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}

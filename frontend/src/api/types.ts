/**
 * API client types shared across frontend.
 */
export interface UserInfo {
  id: string;
  phone: string;
  email: string | null;
  role: 'student' | 'teacher' | 'parent' | 'admin' | 'super_admin';
  full_name: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: UserInfo;
}

export interface OTPResponse {
  message: string;
  expires_in: number;
}

export interface VerifyOTPResponse {
  access_token?: string;
  refresh_token?: string;
  requires_totp?: boolean;
  temp_token?: string;
  requires_registration?: boolean;
  totp_setup_needed?: boolean;
  user?: UserInfo;
}

export interface DashboardModule {
  name: string;
  label: string;
  status: string;
}

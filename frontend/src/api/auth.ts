/**
 * Auth API calls.
 */
import apiClient from './client';
import type { OTPResponse, VerifyOTPResponse } from './types';

export async function requestOTP(phone: string): Promise<OTPResponse> {
  const { data } = await apiClient.post('/auth/request-otp', { phone });
  return data;
}

export async function verifyOTP(
  phone: string,
  otp: string,
  fullName?: string,
  role?: string,
  grade?: number,
): Promise<VerifyOTPResponse> {
  const { data } = await apiClient.post('/auth/verify-otp', {
    phone,
    otp,
    full_name: fullName,
    role,
    grade,
  });
  return data;
}

export async function verifyTOTP(tempToken: string, totpCode: string) {
  const { data } = await apiClient.post('/auth/verify-totp', {
    temp_token: tempToken,
    totp_code: totpCode,
  });
  return data;
}

export async function getMe() {
  const { data } = await apiClient.get('/auth/me');
  return data;
}

/**
 * Gateway configuration from environment variables.
 */
export const config = {
  port: parseInt(process.env.PORT || "4000", 10),
  backendUrl: process.env.BACKEND_URL || "http://backend:8000",
  jwtSecret: process.env.JWT_SECRET || "change_me_to_a_long_random_string",
  redisUrl: process.env.REDIS_URL || "redis://redis:6379/0",
  corsOrigins: (process.env.CORS_ORIGINS || "http://localhost:5173").split(","),
  whatsappWebhookVerifyToken:
    process.env.WHATSAPP_WEBHOOK_VERIFY_TOKEN || "dev_verify_token",
};

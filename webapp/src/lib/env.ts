// Environment configuration for the webapp
export const ENV = {
  DATABASE_URL: process.env.DATABASE_URL || "",
};

export function validateEnv() {
  if (!ENV.DATABASE_URL) {
    throw new Error("NEON_POSTGRES environment variable is required");
  }
}

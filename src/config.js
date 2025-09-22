import dotenv from "dotenv";
dotenv.config();

const required = (name) => {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env: ${name}`);
  return v;
};

export const config = {
  env: process.env.NODE_ENV || "development",
  port: parseInt(process.env.PORT || "10000", 10),
  toolSecret: process.env.TOOL_SECRET || "",
  logLevel: process.env.LOG_LEVEL || "info",
  hotelrunner: {
    base: process.env.HOTELRUNNER_BASE || "https://api2.hotelrunner.com",
    availabilityPath: process.env.HOTELRUNNER_AVAILABILITY_PATH || "/api/v1/availability/search",
    token: required("HOTELRUNNER_TOKEN"),
    id: required("HOTELRUNNER_ID"),
  },
};
